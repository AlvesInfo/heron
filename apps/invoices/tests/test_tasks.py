"""Tests des tâches celery de facturation (appelées directement, fonctions métier patchées)"""
import logging
import smtplib

import pytest

from apps.core.exceptions import EmailException
from apps.invoices import tasks
from apps.invoices.tests.helpers_views import FakeTrace
from conftest import patched_attrs, raising_once

pytestmark = pytest.mark.django_db


@pytest.fixture
def user(make_user):
    return make_user()


@pytest.fixture
def progress(make_sse_progress, user):
    return make_sse_progress(user=user, total_items=3)


def refresh(progress):
    progress.refresh_from_db()
    return progress


# INSERTIONS =======================================================================================
def test_launch_invoices_insertions_succes(make_action, progress, user, monkeypatch):
    action = make_action("insertion_invoices")
    trace = FakeTrace()
    calls = []

    def fake_insertion(user_uuid, invoice_date, job_id):
        calls.append((user_uuid, invoice_date, job_id))
        return trace, "ok\n"

    with patched_attrs(monkeypatch, tasks, invoices_insertion=fake_insertion):
        result = tasks.launch_invoices_insertions(str(user.uuid_identification), "2026-01-31", progress.job_id)

    assert calls == [(str(user.uuid_identification), "2026-01-31", progress.job_id)]
    assert trace.created_by == user
    assert trace.invoices is True
    assert trace.saved == 1
    assert refresh(progress).status == "completed"
    action.refresh_from_db()
    assert action.in_progress is False
    assert "launch_invoices_insertions : " in result


def test_launch_invoices_insertions_sans_job(make_action, user, monkeypatch):
    """Sans job_id rien n'est inséré et la trace reste à None (plus de str() dans le finally)"""
    make_action("insertion_invoices")
    with patched_attrs(monkeypatch, tasks, invoices_insertion=lambda *a: (_ for _ in ()).throw(AssertionError)):
        result = tasks.launch_invoices_insertions(str(user.uuid_identification), "2026-01-31")

    assert "launch_invoices_insertions : " in result


def test_launch_invoices_insertions_type_error(make_action, progress, user, monkeypatch, caplog):
    make_action("insertion_invoices")
    trace = FakeTrace(fail_created_by=True)

    with patched_attrs(monkeypatch, tasks, invoices_insertion=lambda *a: (trace, "")), caplog.at_level(logging.ERROR):
        tasks.launch_invoices_insertions(str(user.uuid_identification), "2026-01-31", progress.job_id)

    assert "TypeError" in caplog.text
    assert trace.errors is True
    assert "Une erreur" in trace.comment
    assert trace.saved == 1


def test_launch_invoices_insertions_exception(make_action, progress, user, monkeypatch, caplog):
    make_action("insertion_invoices")
    with raising_once(RuntimeError("boom")) as boom, patched_attrs(
        monkeypatch, tasks, invoices_insertion=boom
    ), caplog.at_level(logging.ERROR):
        tasks.launch_invoices_insertions(str(user.uuid_identification), "2026-01-31", progress.job_id)

    assert refresh(progress).status == "failed"
    assert "Exception Générale" in caplog.text


def test_launch_invoices_insertions_jauge_inconnue(make_action, user, monkeypatch, caplog):
    make_action("insertion_invoices")
    with patched_attrs(monkeypatch, tasks, invoices_insertion=lambda *a: (FakeTrace(), "")), caplog.at_level(logging.ERROR):
        tasks.launch_invoices_insertions(str(user.uuid_identification), "2026-01-31", "inconnu")

    assert "Impossible de marquer le SSEProgress" in caplog.text


# PDF ==============================================================================================
def test_launch_celery_pdf_launch(progress, user, make_sale_invoice, celery_recorder, monkeypatch):
    make_sale_invoice("AF0001", global_invoice_file="AF0001.pdf")
    make_sale_invoice("AF0002", invoice_number="FV2", global_invoice_file="AF0002.pdf")
    recorder = celery_recorder(tasks)
    updates = []

    with patched_attrs(monkeypatch, tasks, process_update=lambda: updates.append("maj")):
        tasks.launch_celery_pdf_launch(str(user.pk), progress.job_id)

    assert updates == ["maj"]
    assert [kw["cct"] for _, kw in recorder.signatures] == ["AF0001", "AF0002"]
    assert refresh(progress).status == "completed"


def test_launch_celery_pdf_launch_erreur(progress, user, celery_recorder, monkeypatch, caplog):
    celery_recorder(tasks, raise_on_get=RuntimeError("celery down"))

    with patched_attrs(monkeypatch, tasks, process_update=lambda: None), caplog.at_level(logging.ERROR):
        tasks.launch_celery_pdf_launch(str(user.pk), progress.job_id)

    assert refresh(progress).status == "failed"
    assert "launch_celery_pdf_launch" in caplog.text


def test_launch_celery_pdf_launch_jauge_inconnue(user, celery_recorder, caplog):
    celery_recorder(tasks)

    with caplog.at_level(logging.ERROR):
        tasks.launch_celery_pdf_launch(str(user.pk), "inconnu")

    assert "Impossible de marquer le SSEProgress" in caplog.text


def test_launch_generate_pdf_invoices_succes(progress, user, monkeypatch):
    trace = FakeTrace()
    with patched_attrs(monkeypatch, tasks, invoices_pdf_generation=lambda cct, num: (trace, "pdf ok\n")):
        result = tasks.launch_generate_pdf_invoices("AF0001", "AF0001.pdf", user.pk, progress.job_id)

    assert trace.created_by == user
    assert trace.saved == 1
    assert refresh(progress).processed_items == 1
    assert "cct : AF0001" in result["Generation facture pdf : "]


def test_launch_generate_pdf_invoices_type_error(progress, user, monkeypatch, caplog):
    trace = FakeTrace(fail_created_by=True)
    with patched_attrs(monkeypatch, tasks, invoices_pdf_generation=lambda cct, num: (trace, "")), caplog.at_level(logging.ERROR):
        tasks.launch_generate_pdf_invoices("AF0001", "AF0001.pdf", user.pk, progress.job_id)

    assert trace.errors is True
    assert trace.saved == 1
    assert refresh(progress).failed_items == 1
    assert "TypeError" in caplog.text


def test_launch_generate_pdf_invoices_exception(progress, user, monkeypatch, caplog):
    with raising_once(RuntimeError("boom")) as boom, patched_attrs(
        monkeypatch, tasks, invoices_pdf_generation=boom
    ), caplog.at_level(logging.ERROR):
        tasks.launch_generate_pdf_invoices("AF0001", "AF0001.pdf", user.pk, progress.job_id)

    assert "Exception Générale" in caplog.text
    assert refresh(progress).failed_items == 0


# FACTUR-X =========================================================================================
def test_launch_celery_facturx_launch(progress, user, make_sale_invoice, celery_recorder):
    make_sale_invoice("AF0001", printed=True, global_invoice_file="AF0001.pdf")
    recorder = celery_recorder(tasks)

    tasks.launch_celery_facturx_launch(str(user.pk), progress.job_id)

    assert [name for name, _ in recorder.signatures] == ["launch_generate_facturx_invoices"]
    assert refresh(progress).status == "completed"


def test_launch_celery_facturx_launch_erreur(progress, user, celery_recorder, caplog):
    celery_recorder(tasks, raise_on_get=RuntimeError("celery down"))

    with caplog.at_level(logging.ERROR):
        tasks.launch_celery_facturx_launch(str(user.pk), progress.job_id)

    assert refresh(progress).status == "failed"


def test_launch_celery_facturx_launch_jauge_inconnue(user, celery_recorder, caplog):
    celery_recorder(tasks)

    with caplog.at_level(logging.ERROR):
        tasks.launch_celery_facturx_launch(str(user.pk), "inconnu")

    assert "Impossible de marquer le SSEProgress" in caplog.text


@pytest.mark.parametrize("trace_errors", [False, True])
def test_launch_generate_facturx_invoices(progress, user, monkeypatch, trace_errors):
    trace = FakeTrace(errors=trace_errors)
    with patched_attrs(monkeypatch, tasks, invoices_facturx_generation=lambda cct, num: (trace, "")):
        result = tasks.launch_generate_facturx_invoices("AF0001", "AF0001.pdf", user.pk, progress.job_id)

    assert trace.saved == 1
    assert trace.created_by == user
    assert refresh(progress).failed_items == (1 if trace_errors else 0)
    assert "cct : AF0001" in result["Generation Factur-X : "]


def test_launch_generate_facturx_invoices_erreurs(progress, user, monkeypatch, caplog):
    trace = FakeTrace(fail_created_by=True)
    with patched_attrs(monkeypatch, tasks, invoices_facturx_generation=lambda cct, num: (trace, "")), caplog.at_level(logging.ERROR):
        tasks.launch_generate_facturx_invoices("AF0001", "AF0001.pdf", user.pk, progress.job_id)

    assert trace.errors is True
    assert "TypeError" in caplog.text

    with raising_once(RuntimeError("boom")) as boom, patched_attrs(
        monkeypatch, tasks, invoices_facturx_generation=boom
    ), caplog.at_level(logging.ERROR):
        tasks.launch_generate_facturx_invoices("AF0001", "AF0001.pdf", user.pk, progress.job_id)

    assert "Exception Générale" in caplog.text
    assert refresh(progress).failed_items == 2


# ENVOI DES MAILS ==================================================================================
def test_launch_celery_send_invoice_mails_toutes(user, make_email, make_sale_invoice, celery_recorder):
    make_email()
    make_sale_invoice("AF0001", printed=True, global_invoice_file="AF0001.pdf")
    make_sale_invoice("AF0002", invoice_number="FV2", printed=True, send_email=True)
    recorder = celery_recorder(tasks)

    tasks.launch_celery_send_invoice_mails(str(user.pk))

    assert recorder.applied == 1
    assert [kw["context_dict"]["cct"] for _, kw in recorder.signatures] == ["AF0001"]
    assert recorder.signatures[0][1]["context_dict"]["email_text"].strip() == "Bonjour,voici vos factures."


def test_launch_celery_send_invoice_mails_un_cct(user, make_email, make_sale_invoice, celery_recorder):
    make_email()
    make_sale_invoice("AF0001", printed=True, send_email=True, global_invoice_file="AF0001.pdf")
    recorder = celery_recorder(tasks)

    tasks.launch_celery_send_invoice_mails(str(user.pk), cct="AF0001", period="2026-01-01")

    assert [kw["context_dict"]["cct"] for _, kw in recorder.signatures] == ["AF0001"]


def test_launch_celery_send_invoice_mails_erreurs(user, make_email, celery_recorder, monkeypatch, caplog):
    make_email()
    recorder = celery_recorder(tasks)

    class _Group:
        def __init__(self, *tasks):
            pass

        def apply_async(self):
            raise smtplib.SMTPException("smtp")

    user_pk = str(user.pk)

    with patched_attrs(monkeypatch, tasks, group=_Group), pytest.raises(EmailException):
        tasks.launch_celery_send_invoice_mails(user_pk)

    class _GroupBoom(_Group):
        def apply_async(self):
            raise RuntimeError("boom")

    with patched_attrs(monkeypatch, tasks, group=_GroupBoom), caplog.at_level(logging.ERROR):
        tasks.launch_celery_send_invoice_mails(str(user.pk))

    assert "launch_celery_send_invoice_mails" in caplog.text
    assert recorder.applied == 0


def test_send_invoice_email(user, monkeypatch, caplog):
    trace = FakeTrace()
    context = {"cct": "AF0001"}
    with patched_attrs(monkeypatch, tasks, invoices_send_by_email=lambda ctx: (trace, "envoyé\n")):
        result = tasks.send_invoice_email(context, user.pk)

    assert trace.created_by == user
    assert trace.saved == 1
    assert "cct : AF0001" in result["Envoie de la facture par mail : "]

    with patched_attrs(monkeypatch, tasks, invoices_send_by_email=lambda ctx: (FakeTrace(fail_created_by=True), "")), caplog.at_level(logging.ERROR):
        tasks.send_invoice_email(context, user.pk)

    assert "TypeError" in caplog.text

    with raising_once(RuntimeError("boom")) as boom, patched_attrs(
        monkeypatch, tasks, invoices_send_by_email=boom
    ), caplog.at_level(logging.ERROR):
        tasks.send_invoice_email(context, user.pk)

    assert "Exception Générale" in caplog.text


# EXPORT X3 ========================================================================================
def test_launch_export_x3(user, monkeypatch, caplog):
    trace = FakeTrace()
    with patched_attrs(monkeypatch, tasks, export_files_x3=lambda *a: (trace, "export\n")):
        assert tasks.launch_export_x3("sale", "AC00", "AC00_1.txt", user.pk) is True

    assert trace.created_by == user
    assert trace.saved == 1

    with patched_attrs(monkeypatch, tasks, export_files_x3=lambda *a: (FakeTrace(fail_created_by=True), "")), caplog.at_level(logging.ERROR):
        assert tasks.launch_export_x3("sale", "AC00", "AC00_1.txt", user.pk) is False

    assert "TypeError" in caplog.text


def test_launch_export_x3_exception(user, monkeypatch, caplog):
    """Exception avant la création de la trace : la tâche renvoie False (plus d'AttributeError)"""
    with raising_once(RuntimeError("boom")) as boom, patched_attrs(
        monkeypatch, tasks, export_files_x3=boom
    ), caplog.at_level(logging.ERROR):
        assert tasks.launch_export_x3("sale", "AC00", "AC00_1.txt", user.pk) is False

    assert "Exception Générale: launch_export_x3" in caplog.text


# ESSAIS ===========================================================================================
def test_launch_celery_send_emails_essais(user, make_email, celery_recorder, monkeypatch, caplog):
    make_email()
    recorder = celery_recorder(tasks)

    tasks.launch_celery_send_emails_essais(str(user.pk))

    assert recorder.applied == 1
    assert len(recorder.signatures) == 6
    assert {kw["context_dict"]["email_list"] for _, kw in recorder.signatures} == {"admin.bi@acuitis.com", "sav.acuitis@alves-info.fr"}

    class _Group:
        def __init__(self, *tasks):
            pass

        def apply_async(self):
            raise ValueError("adresse")

    user_pk = str(user.pk)

    with patched_attrs(monkeypatch, tasks, group=_Group), pytest.raises(EmailException):
        tasks.launch_celery_send_emails_essais(user_pk)

    class _GroupBoom(_Group):
        def apply_async(self):
            raise RuntimeError("boom")

    with patched_attrs(monkeypatch, tasks, group=_GroupBoom), caplog.at_level(logging.ERROR):
        tasks.launch_celery_send_emails_essais(str(user.pk))

    assert "launch_celery_send_emails_essais" in caplog.text


def test_send_invoice_email_essais(user, monkeypatch, caplog):
    trace = FakeTrace()
    with patched_attrs(monkeypatch, tasks, essais_send_by_email=lambda ctx: (trace, "")):
        result = tasks.send_invoice_email_essais({"cct": "essai"}, user.pk)

    assert trace.saved == 1
    assert "cct : essai" in result["Envoie de la facture par mail : "]

    with patched_attrs(monkeypatch, tasks, essais_send_by_email=lambda ctx: (FakeTrace(fail_created_by=True), "")), caplog.at_level(logging.ERROR):
        tasks.send_invoice_email_essais({"cct": "essai"}, user.pk)

    assert "TypeError" in caplog.text

    with raising_once(RuntimeError("boom")) as boom, patched_attrs(
        monkeypatch, tasks, essais_send_by_email=boom
    ), caplog.at_level(logging.ERROR):
        tasks.send_invoice_email_essais({"cct": "essai"}, user.pk)

    assert "send_invoice_email_essais" in caplog.text
