"""Tests des vues de lancement de la facturation (insertions, pdf, Factur-X, envois, finalisation)"""
import datetime
import logging
import types
import zipfile

import pytest
from django.test import RequestFactory
from django.urls import reverse

from apps.core.models import SSEProgress
from apps.edi.models import EdiValidation
from apps.invoices.bin.facturx_client import FacturXClientError
from apps.invoices.views import launch_invoices_views as views
from conftest import patched_attrs

pytestmark = pytest.mark.django_db


@pytest.fixture
def checks(monkeypatch):
    """Contrôles externes pilotables : finalisation, manquants, process en cours, emails"""
    state = types.SimpleNamespace(
        not_finalize=False, missings=[], in_progress=(False, False, False), emails=[], facturx_in_progress=False
    )
    with patched_attrs(
        monkeypatch,
        views,
        control_insertion=lambda: state.not_finalize,
        control_alls_missings=lambda: state.missings,
        get_invoices_in_progress=lambda: state.in_progress,
        check_emails_to_send=lambda: state.emails,
        get_facturx_in_progress=lambda: state.facturx_in_progress,
    ):
        yield state


@pytest.fixture
def threads(thread_recorder):
    return thread_recorder(views)


# INSERTIONS =======================================================================================
URL_INSERT = "invoices:generate_invoices_insertions"


@pytest.mark.usefixtures('checks')
def test_insertions_sans_facture(logged_client):
    response = logged_client.get(reverse(URL_INSERT))

    assert response.context["not_finalize"] is True
    assert response.context["news"] is False
    assert logged_client.session["level"] == 50


def test_insertions_non_finalise(logged_client, checks, make_edi_import):
    make_edi_import()
    checks.not_finalize = True
    response = logged_client.get(reverse(URL_INSERT))

    assert response.context["not_finalize"] is True
    assert "news" not in response.context


def test_insertions_manquants(logged_client, checks, make_edi_import):
    make_edi_import()
    checks.missings = [("tiers", "Il manque des tiers X3")]
    response = logged_client.get(reverse(URL_INSERT))

    assert response.context["all_missings"] == checks.missings


@pytest.mark.usefixtures('checks', 'month_period')
def test_insertions_get_ok(logged_client, make_edi_import):
    make_edi_import()
    response = logged_client.get(reverse(URL_INSERT))

    assert response.context["en_cours"] is False
    assert response.context["titre_table"] == "Génération de la facturation"


@pytest.mark.parametrize(("in_progress", "titre"), [
    ((True, False, False), "INSERTION DES FACTURES EN COURS"),
    ((False, True, False), "GENERATION DES PDF EN COURS"),
    ((False, False, True), "EN COURS D'ENVOI PAR MAIL"),
])
def test_insertions_en_cours(logged_client, checks, make_edi_import, in_progress, titre):
    make_edi_import()
    checks.in_progress = in_progress
    response = logged_client.get(reverse(URL_INSERT))

    assert response.context["en_cours"] is True
    assert titre in response.context["titre_table"]


@pytest.mark.usefixtures('checks')
def test_insertions_post_lance_le_thread(logged_client, make_edi_import, month_period, threads):
    make_edi_import()
    response = logged_client.post(reverse(URL_INSERT), {"periode": month_period.value})

    payload = response.json()
    assert payload["success"] is True
    progress = SSEProgress.objects.get(job_id=payload["job_id"])
    assert progress.task_type == "invoices_insertion"
    assert progress.total_items == 15
    assert threads == [(views.invoices_insertion, (logged_client.user.uuid_identification, month_period.dte_f, payload["job_id"]), True)]


@pytest.mark.usefixtures('checks')
def test_insertions_post_invalide(logged_client, make_edi_import, threads):
    make_edi_import()
    response = logged_client.post(reverse(URL_INSERT), {"periode": "x"})

    assert response.status_code == 200
    assert threads == []


# PDF ==============================================================================================
URL_PDF = "invoices:generate_pdf_invoice"


def test_pdf_non_finalise(logged_client, checks):
    checks.not_finalize = True
    response = logged_client.get(reverse(URL_PDF))

    assert response.context["not_finalize"] is True


@pytest.mark.usefixtures('checks')
def test_pdf_rien_a_generer(logged_client):
    response = logged_client.get(reverse(URL_PDF))

    assert response.context["news"] is False
    assert response.context["en_cours"] is False


@pytest.mark.parametrize(("in_progress", "titre"), [
    ((False, False, False), "Génération des factures de ventes en pdf"),
    ((True, False, False), "INSERTION DES FACTURES EN COURS"),
    ((False, True, False), "GENERATION DES PDF EN COURS"),
    ((False, False, True), "EN COURS D'ENVOI PAR MAIL"),
])
def test_pdf_get(logged_client, checks, make_sale_invoice, in_progress, titre):
    make_sale_invoice()
    checks.in_progress = in_progress
    response = logged_client.get(reverse(URL_PDF))

    assert response.context["news"] is True
    assert response.context["en_cours"] is any(in_progress)
    assert titre in response.context["titre_table"]


@pytest.mark.usefixtures('checks')
def test_pdf_post_lance_le_thread(logged_client, make_sale_invoice, threads):
    make_sale_invoice("AF0001")
    make_sale_invoice("AF0002", invoice_number="FV2")
    response = logged_client.post(reverse(URL_PDF))

    payload = response.json()
    progress = SSEProgress.objects.get(job_id=payload["job_id"])
    assert progress.task_type == "generation_pdf_invoices"
    assert progress.total_items == 3
    assert threads == [(views.launch_celery_pdf_launch, (logged_client.user.pk, payload["job_id"]), True)]


# FACTUR-X =========================================================================================
URL_FX = "invoices:generate_facturx_invoice"


@pytest.fixture
def facturx_server(monkeypatch):
    """Client Factur-X factice : health() pilotable"""
    state = types.SimpleNamespace(health={"status": "ok", "version": "1.2"}, error=None)

    class _Client:
        base_url = "http://facturx.local"
        profile = "EN16931"

        def health(self):
            if state.error:
                raise state.error

            return state.health

    with patched_attrs(monkeypatch, views, FacturXClient=_Client):
        yield state


@pytest.mark.usefixtures('checks', 'facturx_server')
def test_facturx_rien_a_generer(logged_client):
    response = logged_client.get(reverse(URL_FX))

    assert response.context["en_cours"] is False
    assert response.context["nb_invoices"] == 0
    assert response.context["server_ok"] is True
    assert response.context["server_version"] == "1.2"


@pytest.mark.usefixtures('checks')
def test_facturx_serveur_indisponible(logged_client, facturx_server, make_sale_invoice, caplog):
    make_sale_invoice(printed=True)
    facturx_server.error = FacturXClientError("down")

    with caplog.at_level(logging.WARNING):
        response = logged_client.get(reverse(URL_FX))

    assert response.context["server_ok"] is False
    assert response.context["news"] is False
    assert "indisponible" in caplog.text

    assert logged_client.post(reverse(URL_FX)).json() == {"success": False, "error": "Le serveur Factur-X est injoignable"}


@pytest.mark.parametrize(("in_progress", "facturx", "titre"), [
    ((True, False, False), False, "INSERTION DES FACTURES EN COURS"),
    ((False, True, False), False, "GENERATION DES PDF EN COURS"),
    ((False, False, True), False, "EN COURS D'ENVOI PAR MAIL"),
    ((False, False, False), True, "GENERATION DES FACTUR-X EN COURS"),
])
@pytest.mark.usefixtures('facturx_server')
def test_facturx_en_cours(logged_client, checks, in_progress, facturx, titre):
    checks.in_progress, checks.facturx_in_progress = in_progress, facturx
    response = logged_client.get(reverse(URL_FX))

    assert response.context["en_cours"] is True
    assert titre in response.context["titre_table"]
    assert logged_client.post(reverse(URL_FX)).json() == {"success": False, "error": "Un traitement est en cours"}


@pytest.mark.usefixtures('checks', 'facturx_server')
def test_facturx_post_lance_le_thread(logged_client, make_sale_invoice, threads):
    make_sale_invoice(printed=True, global_invoice_file="AF0001.pdf")
    response = logged_client.post(reverse(URL_FX))

    payload = response.json()
    progress = SSEProgress.objects.get(job_id=payload["job_id"])
    assert progress.task_type == "generation_facturx_invoices"
    assert progress.total_items == 2
    assert threads == [(views.launch_celery_facturx_launch, (logged_client.user.pk, payload["job_id"]), True)]
    assert logged_client.get(reverse(URL_FX)).context["news"] is True


# LISTE ET TÉLÉCHARGEMENT DES PDF ==================================================================
URL_FILES = "invoices:invoices_pdf_files"


def test_pdf_files_get_sur_periode_en_cours(logged_client, make_edi_validation, make_sale_invoice):
    make_edi_validation(billing_period=datetime.date(2026, 1, 1))
    make_sale_invoice(global_invoice_file="AF0001.pdf")
    response = logged_client.get(reverse(URL_FILES))

    assert response.context["dte_d"] == datetime.date(2026, 1, 1)
    assert response.context["dte_f"] == datetime.date(2026, 1, 31)
    assert response.context["alls"]["global_invoice_file"] == "PDF_ALLS_2026-01-01_2026-01-31.zip"
    assert [row["cct"] for row in response.context["invoices"]] == ["AF0001"]


def test_pdf_files_sans_periode_ouverte(logged_client):
    """Sans EdiValidation ouverte, le mois en cours est proposé (la vue plantait en 500)"""
    response = logged_client.get(reverse(URL_FILES))

    assert response.status_code == 200
    assert response.context["dte_d"].day == 1


def test_pdf_files_post(logged_client, month_period):
    response = logged_client.post(reverse(URL_FILES), {"periode": month_period.value})

    assert response.context["dte_d"].isoformat() == month_period.dte_d


def test_get_pdf_file(logged_client, invoices_dirs, make_sale_invoice):
    (invoices_dirs.sales / "AF0001.pdf").write_bytes(b"%PDF-1.4 test")
    make_sale_invoice(global_invoice_file="AF0001.pdf")

    response = logged_client.get(reverse("invoices:get_pdf_file", kwargs={"file_name": "AF0001.pdf"}))

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response.content == b"%PDF-1.4 test"

    response = logged_client.get(reverse("invoices:get_pdf_file", kwargs={"file_name": "PDF_ALLS_2026-01-01_2026-01-31.zip"}))

    assert response["Content-Disposition"].endswith(".zip")
    assert zipfile.ZipFile(invoices_dirs.sales / "PDF_ALLS_2026-01-01_2026-01-31.zip").namelist() == ["AF0001.pdf"]


def test_get_pdf_file_refuse_sortie_du_repertoire(logged_client, invoices_dirs, caplog):
    """Un nom de fichier remontant hors du répertoire des factures est refusé (PermissionError)"""
    (invoices_dirs.media / "secret.txt").write_text("x")
    request = RequestFactory().get("/")
    request.user = logged_client.user

    with caplog.at_level(logging.ERROR):
        response = views.get_pdf_file(request, "../secret.txt")

    assert response.url == reverse("home")
    assert "get_pdf_file" in caplog.text
    assert logged_client.post(reverse("invoices:get_pdf_file", kwargs={"file_name": "x.pdf"})).url == reverse("home")


# ENVOI DES MAILS ==================================================================================
URL_MAIL = "invoices:send_email_pdf_invoice"


@pytest.mark.usefixtures('checks')
def test_send_email_rien_a_envoyer(logged_client):
    response = logged_client.get(reverse(URL_MAIL))

    assert response.context["news"] is False
    assert response.context["not_finalize"] is True
    assert response.context["en_cours"] is False


def test_send_email_emails_invalides(logged_client, checks, make_sale_invoice):
    make_sale_invoice(printed=True)
    checks.emails = [("mauvais@", "CLI001")]
    response = logged_client.get(reverse(URL_MAIL))

    assert response.context["emails_errors"] is True
    assert response.context["emails_errors_list"] == [("mauvais@", "CLI001")]


@pytest.mark.parametrize(("in_progress", "titre"), [
    ((False, False, False), "Envoi global"),
    ((True, False, False), "INSERTION DE FACTURES EN COURS"),
    ((False, True, False), "GENERATION DE PDF EN COURS"),
    ((False, False, True), "EN COURS D'ENVOI PAR MAIL"),
])
def test_send_email_get(logged_client, checks, make_sale_invoice, in_progress, titre):
    make_sale_invoice(printed=True)
    checks.in_progress = in_progress
    response = logged_client.get(reverse(URL_MAIL))

    assert response.context["en_cours"] is any(in_progress)
    assert titre in response.context["titre_table"]


@pytest.mark.usefixtures('checks')
def test_send_email_post_lance_le_thread(logged_client, make_sale_invoice, threads):
    make_sale_invoice("AF0001", printed=True, global_invoice_file="AF0001.pdf")
    make_sale_invoice("AF0001", printed=True, global_invoice_file="AF0001.pdf", invoice_number="FV2")
    response = logged_client.post(reverse(URL_MAIL))

    payload = response.json()
    progress = SSEProgress.objects.get(job_id=payload["job_id"])
    assert progress.task_type == "send_invoices_emails"
    assert progress.total_items == 1
    assert threads == [(views.send_invoices_emails_gmail, (logged_client.user.pk, payload["job_id"]), True)]


# FINALISATION =====================================================================================
URL_FINAL = "invoices:finalize_period"


@pytest.fixture
def finalize_patches(monkeypatch):
    """Finalisation : fonctions métier enregistrées, SQL des comptes manquants neutralisée"""
    calls = []
    with patched_attrs(
        monkeypatch,
        views,
        set_validations=lambda: calls.append("validations"),
        finalize_global_invoices=lambda user: calls.append(("final", user)),
        articles_acuitis_without_accounts="select * from edi_ediimport where false",
    ):
        yield calls


@pytest.mark.usefixtures('checks', 'finalize_patches')
def test_finalize_nouveaux_articles(logged_client, make_article):
    make_article(new_article=True)
    response = logged_client.get(reverse(URL_FINAL))

    assert response.url == reverse("articles:new_articles_list")
    assert logged_client.session["level"] == 50


@pytest.mark.usefixtures('checks', 'finalize_patches')
def test_finalize_comptes_manquants(logged_client, make_edi_import, monkeypatch):
    make_edi_import()
    with patched_attrs(monkeypatch, views, articles_acuitis_without_accounts="select * from edi_ediimport"):
        response = logged_client.get(reverse(URL_FINAL))

    assert response.url == reverse("articles:articles_without_account_list")


@pytest.mark.usefixtures('checks')
def test_finalize_integrations_non_validees(logged_client, finalize_patches, make_edi_import_control):
    make_edi_import_control(valid=False)
    response = logged_client.get(reverse(URL_FINAL))

    assert response.url == reverse("validation_purchases:integration_purchases")
    assert finalize_patches == ["validations"]


@pytest.mark.usefixtures('checks', 'finalize_patches')
def test_finalize_cct_manquants(logged_client, make_edi_import):
    make_edi_import(cct_uuid_identification=None)
    response = logged_client.get(reverse(URL_FINAL))

    assert response.url == reverse("validation_purchases:without_cct_purchases")


@pytest.mark.usefixtures('checks', 'finalize_patches')
def test_finalize_rien_a_finaliser(logged_client, make_edi_validation):
    validation = make_edi_validation(billing_period=datetime.date(2026, 1, 1))
    response = logged_client.get(reverse(URL_FINAL))

    assert response.status_code == 200
    assert response.context["not_finalize"] is False
    assert response.context["form"].initial["periode"] == "2026-02-01_2026-02-28"
    validation.refresh_from_db()
    assert validation.articles_news
    assert validation.integration
    assert validation.cct
    assert any("rien à finaliser" in str(m) for m in response.context["messages"])


@pytest.mark.usefixtures('checks', 'finalize_patches')
def test_finalize_rien_a_finaliser_message_deja_present(logged_client, make_edi_validation, monkeypatch):
    make_edi_validation()
    with patched_attrs(monkeypatch, views.messages, get_messages=lambda request: ["déjà un message"]):
        response = logged_client.get(reverse(URL_FINAL))

    assert response.status_code == 200
    assert "level" not in logged_client.session


@pytest.mark.usefixtures('finalize_patches')
def test_finalize_exports_x3_manquants(logged_client, checks, make_edi_validation, make_sale_invoice):
    make_edi_validation()
    make_sale_invoice(export=False)
    checks.not_finalize = True
    response = logged_client.get(reverse(URL_FINAL))

    assert response.context["not_finalize"] is False
    assert any("imports X3" in str(m) for m in response.context["messages"])


@pytest.mark.usefixtures('finalize_patches')
def test_finalize_get_pret(logged_client, checks, make_edi_validation, make_sale_invoice, make_invoice):
    make_edi_validation(billing_period=datetime.date(2026, 4, 1))
    make_sale_invoice(export=True)
    make_invoice(export=True)
    checks.not_finalize = True
    response = logged_client.get(reverse(URL_FINAL))

    assert response.context["not_finalize"] is True
    assert response.context["titre_table"].endswith("d'Avril 2026")


def test_finalize_post(logged_client, checks, finalize_patches, make_edi_validation, make_sale_invoice):
    validation = make_edi_validation(billing_period=datetime.date(2026, 1, 1))
    make_sale_invoice(export=True)
    checks.not_finalize = True
    response = logged_client.post(reverse(URL_FINAL), {"periode": "2026-02-01_2026-02-28"})

    assert response.url == reverse(URL_FINAL)
    validation.refresh_from_db()
    assert validation.final is True
    assert validation.final_at is not None
    nouvelle = EdiValidation.objects.get(final=False)
    assert nouvelle.billing_period == datetime.date(2026, 2, 1)
    assert nouvelle.created_by == logged_client.user
    assert finalize_patches == ["validations", ("final", logged_client.user)]
    assert logged_client.session["level"] == 20
