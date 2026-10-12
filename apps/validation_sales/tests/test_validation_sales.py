# pylint: disable=E0401,W0621
"""
FR : Tests de l'app validation_sales (écrans de contrôle des ventes et export des ventes
     Héron non finalisées)
EN : Tests for validation_sales app

created at: 2026-10-12
created by: Paulo ALVES
"""
import datetime
import importlib
import io
from decimal import Decimal
from uuid import uuid4

import pytest
from django.apps import apps as django_apps
from django.urls import reverse
from openpyxl import load_workbook

from apps.core.functions.functions_http_response import CONTENT_TYPE_EXCEL
from apps.validation_sales import urls as sales_urls
from apps.validation_sales.apps import ValidationSalesConfig
from apps.validation_sales.excel_outputs import columns_excel
from apps.validation_sales.excel_outputs import output_excel_sales_not_final_optimized as optimized
from apps.validation_sales.views import views_etape_5_1

pytestmark = pytest.mark.django_db

ROUTES = [pattern.name for pattern in sales_urls.urlpatterns]


def _sheet_rows(file_io):
    file_io.seek(0)
    return [tuple(row) for row in load_workbook(file_io, read_only=True).active.iter_rows(values_only=True)]


@pytest.fixture
def not_final_data(make_maison, make_section, make_sale_invoice, make_sale_invoice_detail, make_invoice_common_details):
    """Une vente non finalisée (une ligne) dont la maison a un axe BU, une vente finalisée ignorée"""
    make_maison("AF0001", axe_bu=make_section("BU", "CAHA"))
    pending = make_sale_invoice("AF0001", "CLI001", final=False, invoice_sage_number="VTE-PENDING", code_center="ACF")
    make_sale_invoice("AF0001", "CLI001", final=True, invoice_sage_number="VTE-FINAL")
    import_uuid = uuid4()
    make_invoice_common_details(
        "FOUR001", "FAC-77", import_uuid_identification=import_uuid, supplier="Fournisseur Un",
        reference_article="ART-1", libelle="Monture", qty=Decimal("2"),
    )
    make_sale_invoice_detail(pending, import_uuid_identification=import_uuid, net_amount=Decimal("80"))
    return pending


def test_app_config_et_routes():
    config = django_apps.get_app_config("validation_sales")

    assert isinstance(config, ValidationSalesConfig)
    assert config.name == "apps.validation_sales"
    assert list(config.get_models()) == []
    assert len(ROUTES) == len(set(ROUTES)) == 16
    assert importlib.import_module("apps.validation_sales.admin") is not None
    assert len(columns_excel.columns_sales_heron) == 40


@pytest.mark.parametrize("route", ROUTES)
def test_ecrans_de_controle(logged_client, route):
    """Tous les écrans (dont les gabarits d'export) s'affichent"""
    response = logged_client.get(reverse(f"validation_sales:{route}"))

    assert response.status_code == 200
    assert response.context["titre_table"]


def test_export_ventes_non_finalisees(not_final_data):
    file_io = io.BytesIO()

    result = optimized.excel_heron_sales_not_final(file_io, "ventes.xlsx")

    rows = _sheet_rows(file_io)
    assert "OK" in result
    assert rows[0][0] == "VENTES HERON A FINALISER"
    data = [row for row in rows if row[3] == "AF0001"]
    assert len(data) == 1
    line = data[0]
    assert line[:3] == ("ACF", "ACF", "VENTE")
    assert line[7] == "VTE-PENDING"
    assert line[14:16] == ("FOUR001", "Fournisseur Un")
    assert (line[17], line[19], line[20], line[21]) == ("FAC-77", "ART-1", "Monture", 2)
    assert line[23] == 80
    assert line[33:36] == ("707000", "CAHA", "607000")


def test_export_sans_axe_bu_ni_ligne(make_maison, make_sale_invoice, make_sale_invoice_detail, make_invoice_common_details):
    """Sans axe BU sur la maison : BU client et compte OD vides"""
    make_maison("AF0002")
    pending = make_sale_invoice("AF0002", "CLI001", final=False)
    import_uuid = uuid4()
    make_invoice_common_details("FOUR001", "FAC-1", import_uuid_identification=import_uuid)
    make_sale_invoice_detail(pending, import_uuid_identification=import_uuid)

    rows = list(optimized.fetch_rows())

    assert len(rows) == 1
    assert rows[0][34:36] == ("", "")

    file_io = io.BytesIO()
    assert "OK" in optimized.excel_heron_sales_not_final(file_io, "vide.xlsx")


def test_fetch_rows_sans_vente():
    assert list(optimized.fetch_rows()) == []


def test_vue_export(logged_client, monkeypatch, not_final_data):
    """POST renvoie le fichier (cookie de fin de téléchargement), GET ou erreur affichent l'écran"""
    url = reverse("validation_sales:invoices_sales_export_globals")

    response = logged_client.post(url, {"download_token": "abc123"})
    assert response.status_code == 200
    assert response["Content-Type"] == CONTENT_TYPE_EXCEL
    assert "VENTES_A_FINALISER_" in response["Content-Disposition"]
    assert response.cookies["download_complete_abc123"].value == "true"

    page = logged_client.get(url)
    assert page.status_code == 200
    assert page.context["titre_table"] == "VENTES HERON NON FINALISEES"

    def _boom(*_args, **_kwargs):
        raise RuntimeError("export cassé")

    monkeypatch.setattr(views_etape_5_1, "response_file", _boom)
    failed = logged_client.post(url, {})
    assert failed.status_code == 200
    assert failed.context["titre_table"] == "VENTES HERON NON FINALISEES"


def test_date_de_facture_dans_export(not_final_data):
    """La date de facture est bien portée dans l'export (contrôle de l'ordre des colonnes)"""
    rows = list(optimized.fetch_rows())

    assert isinstance(rows[0][9], datetime.date)
