"""Tests des vues des étapes 6.0 (exports achats EDI), 6.1 (RFA mensuelles) et des écrans RFA"""

import logging
from pathlib import Path

import pytest
from django.urls import reverse

from apps.validation_purchases.views import views_etape_6_0, views_etape_6_1
from conftest import patched_attrs

pytestmark = pytest.mark.django_db


def url(name, **kwargs):
    return reverse(f"validation_purchases:{name}", kwargs=kwargs or None)


def test_suppliers_edi_purchases(logged_client):
    response = logged_client.get(url("suppliers_edi_purchases"))

    assert response.status_code == 200
    assert response.context["titre_table"].startswith("6.0")


def test_edi_import_purchases_export(logged_client, stub_excel, caplog):
    stub_excel(views_etape_6_0, "excel_heron_purchases_edi_import")

    response = logged_client.get(url("edi_import_purchases_export"))
    assert response["Content-Disposition"].startswith("attachment; filename=FACTURES FOURNISSEURS_")

    stub_excel(views_etape_6_0, "excel_heron_purchases_edi_import", error=RuntimeError("boom"))
    with caplog.at_level(logging.ERROR, logger="error_views"):
        response = logged_client.get(url("edi_import_purchases_export"))

    assert response.status_code == 200
    assert response.context["titre_table"].startswith("6.0")
    assert "edi_import_purchases_export" in caplog.text


def test_edi_import_purchases_export_csv(logged_client, tmp_path, monkeypatch, settings, caplog):
    written = []

    def fake_csv(emplacement: Path):
        written.append(emplacement)
        emplacement.write_text("a;b\n1;2\n", encoding="utf8")
        return {"OK": "ok"}

    settings.MEDIA_EXCEL_FILES_DIR = tmp_path

    with patched_attrs(monkeypatch, views_etape_6_0, csv_heron_purchases_edi_import=fake_csv):
        response = logged_client.get(url("edi_import_purchases_export_csv"))

    assert response.status_code == 200
    assert response["Content-Disposition"] == 'attachment; filename="FACTURES FOURNISSEURS.csv"'
    assert b"".join(response.streaming_content) == b"a;b\n1;2\n"
    assert written == [tmp_path / "FACTURES FOURNISSEURS.csv"]

    def boom(emplacement):
        raise RuntimeError("boom")

    with (
        patched_attrs(
            monkeypatch,
            views_etape_6_0,
            MEDIA_EXCEL_FILES_DIR=tmp_path,
            csv_heron_purchases_edi_import=boom,
        ),
        caplog.at_level(logging.ERROR, logger="error_views"),
    ):
        response = logged_client.get(url("edi_import_purchases_export_csv"))

    assert response.status_code == 200
    assert response.context["titre_table"].startswith("6.0")


def test_rfa_mensuelles(logged_client):
    response = logged_client.get(url("rfa_mensuelles"))

    assert response.status_code == 200
    assert response.context["titre_table"].startswith("6.1")


def test_rfa_generated_export(logged_client, stub_excel, caplog):
    stub_excel(views_etape_6_1, "excel_rfa_mensuelles")

    response = logged_client.get(url("rfa_generated_export"))
    assert response["Content-Disposition"].startswith("attachment; filename=RFA_MENSUELLES_")

    stub_excel(views_etape_6_1, "excel_rfa_mensuelles", error=RuntimeError("boom"))
    with caplog.at_level(logging.ERROR, logger="error_views"):
        response = logged_client.get(url("rfa_generated_export"))

    assert response.status_code == 302
    assert response.url == url("rfa_mensuelles")
    assert "rfa_generated_export" in caplog.text


@pytest.mark.parametrize(
    ("name", "title"),
    [
        ("rfa_cct_invoices_purchases", "Controle des RFA par CCT- Achats"),
        ("rfa_cct_invoices_purchases_export", "Export Excel"),
        ("rfa_prj_invoices_purchases", "Controle des RFA par PRJ - Achats"),
        ("rfa_prj_invoices_purchases_export", "Export Excel"),
    ],
)
def test_rfa_views(logged_client, name, title):
    response = logged_client.get(url(name))

    assert response.status_code == 200
    assert response.context["titre_table"] == title
