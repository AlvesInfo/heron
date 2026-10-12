"""Tests des vues de génération et de téléchargement des exports X3"""

import logging
import zipfile

import pytest
from django.test import RequestFactory
from django.urls import reverse

from apps.invoices.models import ExportX3, Invoice, SaleInvoice
from apps.invoices.views import export_x3_invoices_views as views

pytestmark = pytest.mark.django_db
URL = "invoices:generate_exports_X3"


def test_rien_a_exporter(logged_client):
    response = logged_client.get(reverse(URL))

    assert response.context["export"] is False
    assert logged_client.session["level"] == 50


def test_get_avec_factures(logged_client, make_sale_invoice):
    make_sale_invoice()
    response = logged_client.get(reverse(URL))

    assert response.context["export"] is True


@pytest.mark.usefixtures("export_counters")
def test_post_succes(
    logged_client,
    make_sale_invoice,
    make_invoice,
    make_edi_validation,
    invoices_dirs,
    celery_recorder,
):
    make_sale_invoice()
    make_invoice()
    make_edi_validation()
    recorder = celery_recorder(views)
    # un seul fichier produit par les tâches (les autres sont absents)
    (invoices_dirs.export / "AC00_00001.txt").write_text("odana")

    response = logged_client.post(reverse(URL))

    assert response.status_code == 200
    assert [name for name, _ in recorder.signatures] == ["launch_export_x3"] * 6
    assert [kw["export_type"] for _, kw in recorder.signatures] == [
        "odana",
        "sale",
        "purchase",
        "gdaud",
        "sdoa",
        "do",
    ]
    export = ExportX3.objects.get()
    assert export.odana_file.name == "AC00_00001.txt"
    assert export.sale_file.name == ""
    assert export.purchase_file.name == ""
    assert export.alls_zip_file.name.startswith("AC00_")
    assert export.alls_zip_file.name.endswith("00005.zip")
    assert zipfile.ZipFile(invoices_dirs.export / export.alls_zip_file.name).namelist() == [
        "AC00_00001.txt"
    ]
    assert SaleInvoice.objects.filter(export=True).count() == 1
    assert Invoice.objects.filter(export=True).count() == 1
    assert logged_client.session["level"] == 20


@pytest.mark.usefixtures("export_counters")
def test_post_erreur(logged_client, make_sale_invoice, invoices_dirs, celery_recorder, caplog):
    make_sale_invoice()
    celery_recorder(views, results=[True, False, True, True, True, True])
    (invoices_dirs.export / "AC00_00001.txt").write_text("odana")

    with caplog.at_level(logging.WARNING):
        response = logged_client.post(reverse(URL))

    assert response.status_code == 200
    assert not (invoices_dirs.export / "AC00_00001.txt").exists()
    assert not ExportX3.objects.exists()
    assert SaleInvoice.objects.filter(export=True).count() == 0
    assert logged_client.session["level"] == 50


def test_export_x3_files_list(logged_client, make_export_x3):
    make_export_x3()
    response = logged_client.get(reverse("invoices:export_x3_files"))

    assert response.status_code == 200
    assert len(response.context["exports"]) == 1
    assert "order" in response.context["datatable_ordering"]


def test_get_export_x3_file(logged_client, invoices_dirs, caplog):
    (invoices_dirs.export / "AC00_1.txt").write_text("T;1")
    response = logged_client.get(
        reverse("invoices:get_export_x3_file", kwargs={"file_name": "AC00_1.txt"})
    )

    assert response.status_code == 200
    assert response.content == b"T;1"
    assert response["Content-Disposition"] == "attachment; filename=AC00_1.txt"

    (invoices_dirs.media / "secret.txt").write_text("x")
    request = RequestFactory().get("/")
    request.user = logged_client.user
    with caplog.at_level(logging.ERROR):
        response = views.get_export_x3_file(request, "../secret.txt")

    assert response.url == reverse("home")
    assert "get_export_x3_file" in caplog.text
    assert logged_client.post(
        reverse("invoices:get_export_x3_file", kwargs={"file_name": "AC00_1.txt"})
    ).url == reverse("home")
