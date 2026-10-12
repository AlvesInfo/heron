# pylint: disable=E0401,W0621,W0611
"""Tests de l'envoi des factures par email (SMTP via apps.core) et de la boucle Gmail"""

import logging

import pytest

from apps.core.exceptions import EmailException
from apps.invoices.bin import send_emails_essais, send_invoices_emails
from apps.invoices.loops import send_emails_with_gmail
from apps.invoices.tests.helpers_external import INVOICE_MONTH, PDF_BYTES, reload_with_node
from conftest import patched_attrs, raising_once

pytestmark = pytest.mark.django_db


@pytest.fixture
def mass_mail(monkeypatch):
    """Remplace l'envoi SMTP réel par un enregistreur"""
    sent = []

    def _send(email_list):
        sent.extend(email_list)
        return {"ok"}

    monkeypatch.setattr(send_invoices_emails, "send_mass_mail", _send)
    monkeypatch.setattr(send_emails_essais, "send_mass_mail", _send)
    return sent


# invoices_send_by_email ===========================================================================
def test_invoices_send_by_email(sale_for_email, make_sale_invoice, mass_mail):
    """Les emails valides du tiers et de la maison sont destinataires, les factures sont flaguées"""
    sale, context_dict = sale_for_email(emails=("client@heron.local", "", "pas-un-email"))
    second = make_sale_invoice(
        cct="AF0001",
        third_party_num="CLI001",
        printed=True,
        global_invoice_file="AF0001_global.pdf",
        invoice_month=INVOICE_MONTH,
    )

    trace, to_print = send_invoices_emails.invoices_send_by_email(context_dict)

    second.refresh_from_db()
    assert second.send_email is True

    assert to_print.startswith("Have send invoice email : AF0001_global.pdf")
    assert trace.errors is False
    assert trace.file_name == "send email invoice : AF0001_global.pdf"
    assert trace.time_to_process >= 0
    mail_to, subject, _, _, context, attachments = mass_mail[0]
    assert sorted(mail_to) == ["client@heron.local", "maison@heron.local"]
    assert subject == "Factures {periode}"
    assert context["periode"] == "JANVIER 2026"
    assert context["cct"] == "AF0001 - Maison Paris"
    assert "N°: " + sale.invoice_sage_number in context["factures"]
    assert context["centrale"] == "Centrale : Centrale ACF"
    assert attachments[0].read_bytes() == PDF_BYTES
    sale.refresh_from_db()
    assert sale.send_email is True


def test_invoices_send_by_email_sans_adresse(sale_for_email, mass_mail):
    sale, context_dict = sale_for_email(emails=(), maison_email=None)

    trace, to_print = send_invoices_emails.invoices_send_by_email(context_dict)

    assert to_print.startswith("Error - Have Not send invoice email")
    assert trace.errors is True
    assert "Pas d'adresses mail pour le client : AF0001 - Maison Paris" in trace.comment
    assert trace.comment.count("Une erreur c'est produite") == 1
    assert mass_mail == []
    sale.refresh_from_db()
    assert sale.send_email is False


@pytest.mark.parametrize(
    ("exception", "logged"),
    [(EmailException("smtp"), "EmailException"), (RuntimeError("boom"), "Exception Générale")],
)
def test_invoices_send_by_email_erreurs_envoi(
    sale_for_email, monkeypatch, caplog, exception, logged
):
    _, context_dict = sale_for_email()

    with (
        raising_once(exception) as boom,
        patched_attrs(monkeypatch, send_invoices_emails, send_mass_mail=boom),
        caplog.at_level(logging.ERROR, logger="send_email"),
    ):
        trace, _ = send_invoices_emails.invoices_send_by_email(context_dict)

    assert trace.errors is True
    assert logged in caplog.text
    assert str(context_dict) in trace.comment


# essais_send_by_email =============================================================================
@pytest.mark.usefixtures("email_dirs")
def test_essais_send_by_email(mass_mail):
    context_dict = {
        "invoice_month": "2026-01-01",
        "email_list": "essai@heron.local",
        "cct": "AF0001",
        "global_invoice_file": "un.pdf",
        "subject_email": "s",
        "email_text": "t",
        "email_html": "h",
    }

    trace, to_print = send_emails_essais.essais_send_by_email(context_dict)

    assert to_print.startswith("Have send invoice email : un.pdf")
    assert mass_mail[0][0] == ["essai@heron.local"]
    assert mass_mail[0][4]["factures"].startswith("facttures<p")
    assert trace.errors is False


@pytest.mark.usefixtures("email_dirs")
def test_essais_send_by_email_sans_adresse_et_erreurs(monkeypatch, caplog):
    context_dict = {
        "invoice_month": "2026-01-01",
        "email_list": "",
        "cct": "AF0001",
        "global_invoice_file": "un.pdf",
    }

    trace, to_print = send_emails_essais.essais_send_by_email(context_dict)

    assert to_print.startswith("Error - Have Not send")
    assert trace.errors is True

    context_dict["email_list"] = "essai@heron.local"

    for exception in (EmailException("smtp"), RuntimeError("boom")):
        with (
            raising_once(exception) as boom,
            patched_attrs(monkeypatch, send_emails_essais, send_mass_mail=boom),
            caplog.at_level(logging.ERROR, logger="send_email"),
        ):
            trace, _ = send_emails_essais.essais_send_by_email(context_dict)

        assert trace.errors is True


# send_emails_with_gmail ===========================================================================
@pytest.fixture
def celery_group(monkeypatch):
    """Remplace group / celery_app.signature : enregistre les signatures, renvoie le résultat voulu"""
    state = {"signatures": [], "result": {"sent": 1}, "error": None}

    def signature(name, kwargs):
        state["signatures"].append((name, kwargs))
        return (name, kwargs)

    class _Group:
        def __init__(self, *signatures):
            self.signatures = signatures

        def __call__(self):
            return self

        def get(self, timeout):
            if state["error"]:
                raise state["error"]
            return state["result"]

    monkeypatch.setattr(send_emails_with_gmail, "group", _Group)
    monkeypatch.setattr(
        send_emails_with_gmail,
        "celery_app",
        type("App", (), {"signature": staticmethod(signature)}),
    )
    return state


def test_send_invoices_emails_gmail(make_user, make_sse_progress, celery_group):
    user = make_user()
    progress = make_sse_progress(user=user)

    error, info = send_emails_with_gmail.send_invoices_emails_gmail(user.pk, progress.job_id)

    assert (error, info) == (False, "{'sent': 1}")
    assert celery_group["signatures"] == [
        ("celery_send_invoices_emails_gmail", {"user_pk": str(user.pk), "job_id": progress.job_id})
    ]
    progress.refresh_from_db()
    assert progress.status == "completed"
    from apps.parameters.models import ActionInProgress

    assert ActionInProgress.objects.get(action="send_mass_mail").in_progress is False


def test_send_invoices_emails_gmail_erreur(make_user, make_sse_progress, celery_group, caplog):
    user = make_user()
    progress = make_sse_progress(user=user)
    celery_group["error"] = RuntimeError("worker down")

    with caplog.at_level(logging.ERROR, logger="send_email"):
        error, info = send_emails_with_gmail.send_invoices_emails_gmail(user.pk, progress.job_id)

    assert error is True
    assert "worker down" in info
    progress.refresh_from_db()
    assert progress.status == "failed"


@pytest.mark.usefixtures("celery_group")
def test_send_invoices_emails_gmail_sans_job_id(make_user):
    error, info = send_emails_with_gmail.send_invoices_emails_gmail(make_user().pk, "")

    assert error is True
    assert "DoesNotExist" in info


@pytest.mark.usefixtures("celery_group")
def test_send_invoices_emails_gmail_jauge_inconnue(make_user, caplog):
    """Sans jauge : l'erreur est journalisée, et le marquage en échec ne peut aboutir"""
    user = make_user()

    with caplog.at_level(logging.ERROR, logger="send_email"):
        error, _ = send_emails_with_gmail.send_invoices_emails_gmail(user.pk, "inexistant")

    assert error is True
    assert "Impossible de marquer le SSEProgress comme failed" in caplog.text


# amorçage des scripts =============================================================================
@pytest.mark.parametrize("module", [send_invoices_emails, send_emails_essais])
@pytest.mark.parametrize(("node", "expected"), [("MSI", "/"), ("serveur", "/home/paulo/heron")])
def test_base_dir_selon_la_machine(monkeypatch, module, node, expected):
    assert reload_with_node(monkeypatch, module, node) == expected
