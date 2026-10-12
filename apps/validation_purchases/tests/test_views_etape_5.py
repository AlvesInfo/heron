"""Tests des vues des étapes 5.0 à 5.5 (refac, fournisseurs M vs M-1, CA, contrôles Sage)"""
import logging
import uuid

import pytest
from django.urls import reverse

from apps.validation_purchases.tests.helpers_views import messages_of
from apps.validation_purchases.views import (
    views_etape_5_0,
    views_etape_5_0A,
    views_etape_5_0B,
    views_etape_5_1,
    views_etape_5_3,
    views_etape_5_3A,
    views_etape_5_5,
)

pytestmark = pytest.mark.django_db
HOME = reverse("home")


def url(name, **kwargs):
    return reverse(f"validation_purchases:{name}", kwargs=kwargs or None)


# 5.0 - REFAC PAR CCT ==============================================================================
@pytest.mark.usefixtures('integration_data')
def test_refac_cct_purchases(logged_client):
    response = logged_client.get(url("refac_cct_purchases"))

    assert response.status_code == 200
    clients = response.context["clients"]
    assert len(clients) == 1
    assert clients[0]["cct_name"] == "AF0001 - Maison AF0001"
    assert clients[0]["M_00"] == 30
    assert list(response.context["mois_dict"]) == ["M3", "M2", "M1", "M0"]
    assert response.context["mois_dict"]["M0"] == "Janvier<br>2026"


def test_refac_cct_purchases_export(logged_client, integration_data, stub_excel, caplog):
    calls = stub_excel(views_etape_5_0, "excel_refac_cct")

    response = logged_client.get(url("refac_cct_purchases_export"))
    assert response["Content-Disposition"].startswith("attachment; filename=CONTROLE_REFAC_M-1_M_PAR_CCT_")
    assert calls[0][1] == ({"initial_date": integration_data.validation.billing_period},)

    stub_excel(views_etape_5_0, "excel_refac_cct", error=RuntimeError("boom"))
    with caplog.at_level(logging.ERROR, logger="error_views"):
        response = logged_client.get(url("refac_cct_purchases_export"))

    assert response.url == url("refac_cct_purchases")


# VALIDATIONS 5.0 / 5.1 / 5.3 ======================================================================
SCREENS = [
    ("refac_cct_validation", "refac_cct", "Le contrôle Refac M M-1 par CCT est maintenant"),
    ("balance_suppliers_purchases_validation", "suppliers", "Le contrôle des fournisseurs est maintenant"),
    ("ca_cct_validation", "validation_ca", "Le contrôle du CA Cosium / Ventes Héron est maintenant"),
]


@pytest.mark.parametrize(("name", "flag", "label"), SCREENS)
def test_validations(ajax_client, logged_client, validation_period, name, flag, label, caplog):
    identification = str(validation_period.uuid_identification)

    response = ajax_client.post(url(name), {"uuid_identification": identification, flag: "on"})
    assert response.json() == {"success": "ok"}
    validation_period.refresh_from_db()
    assert getattr(validation_period, flag) is True
    assert f"{label} validé" in messages_of(response)

    response = ajax_client.post(url(name), {"uuid_identification": identification})
    assert response.json() == {"success": "ko"}
    assert f"{label} invalidé" in messages_of(response)

    assert ajax_client.get(url(name)).url == HOME
    assert logged_client.post(url(name), {}).url == HOME

    with caplog.at_level(logging.ERROR, logger="error_views"):
        unknown = ajax_client.post(url(name), {"uuid_identification": str(uuid.uuid4()), flag: "on"})
        invalid = ajax_client.post(url(name), {flag: "on"})

    assert unknown.json() == {"success": "ko"}
    assert invalid.json() == {"success": "ko"}
    assert f"{name} error" in caplog.text
    assert "form invalid" in caplog.text


# 5.A / 5.B - FOURNISSEURS M VS M-1 PAR CCT ========================================================
def test_suppliers_m_purchases(logged_client, integration_data):
    response = logged_client.get(url("suppliers_m_purchases", client="AF0001"))

    assert response.status_code == 200
    assert response.context["maison"] == integration_data.maison
    clients = response.context["clients"]
    assert len(clients) == 1
    assert clients[0]["tiers"] == "FOUR001 - WIDEX SAS"
    assert clients[0]["M_00"] == 30
    assert list(response.context["mois_dict"]) == ["M3", "M2", "M1", "M0"]


def test_suppliers_m_purchases_maison_inconnue(logged_client):
    assert logged_client.get(url("suppliers_m_purchases", client="ZZ")).status_code == 404


def test_suppliers_m_purchases_export(logged_client, stub_excel, caplog):
    calls = stub_excel(views_etape_5_0A, "excel_suppliers_m_vs_m1")

    response = logged_client.get(url("suppliers_m_purchases_export", client="AF0001"))
    assert response["Content-Disposition"].startswith("attachment; filename=CONTROLE_AF0001_M_VS_M-1_")
    assert calls[0][1] == ("AF0001",)

    stub_excel(views_etape_5_0A, "excel_suppliers_m_vs_m1", error=RuntimeError("boom"))
    with caplog.at_level(logging.ERROR, logger="error_views"):
        response = logged_client.get(url("suppliers_m_purchases_export", client="AF0001"))

    assert response.url == url("suppliers_m_purchases", client="AF0001")


@pytest.mark.usefixtures('integration_data')
def test_third_suppliers_m_purchases(logged_client):
    response = logged_client.get(url("third_suppliers_m_purchases", client="AF0001", third_party_num="FOUR001"))

    assert response.status_code == 200
    clients = response.context["clients"]
    assert [row["invoice_number"] for row in clients] == ["F001", "F002"]
    assert response.context["chevron_retour"] == url("suppliers_m_purchases", client="AF0001")


def test_third_suppliers_m_purchases_export(logged_client, stub_excel, caplog):
    calls = stub_excel(views_etape_5_0B, "excel_third_suppliers_m_vs_m1")
    kwargs = {"client": "AF0001", "third_party_num": "FOUR001"}

    response = logged_client.get(url("third_suppliers_m_purchases_export", **kwargs))
    assert response["Content-Disposition"].startswith("attachment; filename=CONTROLE_AF0001_FOUR001_M_VS_M-1_")
    assert calls[0][1] == ("AF0001", "FOUR001")

    stub_excel(views_etape_5_0B, "excel_third_suppliers_m_vs_m1", error=RuntimeError("boom"))
    with caplog.at_level(logging.ERROR, logger="error_views"):
        response = logged_client.get(url("third_suppliers_m_purchases_export", **kwargs))

    assert response.url == url("third_suppliers_m_purchases", **kwargs)
    assert "third_suppliers_m_purchases_export" in caplog.text


# 5.1 - BALANCE FOURNISSEURS =======================================================================
def test_balance_suppliers_purchases(logged_client, integration_data):
    response = logged_client.get(url("balance_suppliers_purchases"))

    assert response.status_code == 200
    suppliers = response.context["invoices_suppliers"]
    assert len(suppliers) == 1
    assert suppliers[0]["tiers"] == "WIDEX SAS"
    assert suppliers[0]["M_00"] == 30
    assert response.context["suppliers_validation"] == integration_data.validation


def test_balance_suppliers_purchases_export(logged_client, integration_data, stub_excel, caplog):
    calls = stub_excel(views_etape_5_1, "excel_balance_suppliers_purchases")

    response = logged_client.get(url("balance_suppliers_purchases_export"))
    assert response["Content-Disposition"].startswith("attachment; filename=CONTROLE_FACTURES_FOURNISSEURS_")
    assert calls[0][1] == ({"initial_date": integration_data.validation.billing_period},)

    stub_excel(views_etape_5_1, "excel_balance_suppliers_purchases", error=RuntimeError("boom"))
    with caplog.at_level(logging.ERROR, logger="error_views"):
        response = logged_client.get(url("balance_suppliers_purchases_export"))

    assert response.url == url("balance_suppliers_purchases")


# 5.3 / 5.3A - CA COSIUM / VENTES HERON ============================================================
def test_ca_cct(logged_client, validation_period):
    response = logged_client.get(url("ca_cct"))

    assert response.status_code == 200
    assert response.context["clients"] == []
    assert list(response.context["mois_dict"]) == ["M0", "M1"]
    assert response.context["ca_cct_validation"] == validation_period


def test_ca_cct_export(logged_client, stub_excel, caplog):
    stub_excel(views_etape_5_3, "excel_ca_cct")
    assert logged_client.get(url("ca_cct_export"))["Content-Disposition"].startswith("attachment; filename=CONTROLE_CA_CCT_")

    stub_excel(views_etape_5_3, "excel_ca_cct", error=RuntimeError("boom"))
    with caplog.at_level(logging.ERROR, logger="error_views"):
        assert logged_client.get(url("ca_cct_export")).url == url("ca_cct")


@pytest.mark.usefixtures('integration_data')
def test_ca_familly_cct(logged_client):
    response = logged_client.get(url("ca_familly_cct", client="AF0001"))

    assert response.status_code == 200
    assert response.context["clients"] == []
    assert response.context["cct_client"] == "AF0001"
    assert response.context["chevron_retour"] == url("ca_cct")


def test_ca_familly_cct_export(logged_client, stub_excel, caplog):
    calls = stub_excel(views_etape_5_3A, "excel_familly_ca_cct")

    response = logged_client.get(url("ca_familly_cct_export", client="AF0001"))
    assert response["Content-Disposition"].startswith("attachment; filename=CONTROLE_CA_CCT_")
    assert calls[0][1] == ("AF0001",)

    stub_excel(views_etape_5_3A, "excel_familly_ca_cct", error=RuntimeError("boom"))
    with caplog.at_level(logging.ERROR, logger="error_views"):
        response = logged_client.get(url("ca_familly_cct_export", client="AF0001"))

    assert response.url == url("ca_familly_cct", client="AF0001")


# 5.5 - CONTROLES SAGE =============================================================================
@pytest.mark.parametrize(("name", "title", "details", "familles"), [
    ("sage_controls_globals_purchases", "Contrôle Intégration Sage X3 - Achats", None, None),
    ("validation_purchases_export_globals", "Export Excel", None, None),
    ("sage_controls_details_purchases", "Contrôle Intégration Sage X3 - Achats", True, None),
    ("validation_purchases_export_details", "Export Excel", None, None),
    ("sage_controls_familles_purchases", "Contrôle Intégration Sage X3 - Détails Achats", True, True),
    ("validation_purchases_export_familles", "Export Excel", None, None),
])
def test_sage_controls(logged_client, name, title, details, familles):
    response = logged_client.get(url(name))

    assert response.status_code == 200
    assert response.context["titre_table"] == title
    assert response.context.get("details") == details
    assert response.context.get("details_familles") == familles


def test_invoices_purchases_export_globals(logged_client, stub_excel, caplog):
    calls = stub_excel(views_etape_5_5, "excel_heron_purchases_not_final")

    response = logged_client.get(url("invoices_purchases_export_globals"))
    assert response.status_code == 200
    assert response.context["titre_table"] == "ACHATS HERON NON FINALISEES"

    response = logged_client.post(url("invoices_purchases_export_globals"), {"download_token": "tok123"})
    assert response["Content-Disposition"].startswith("attachment; filename=ACHATS_A_FINALISER_")
    assert response.cookies["download_complete_tok123"].value == "true"
    assert len(calls) == 1

    stub_excel(views_etape_5_5, "excel_heron_purchases_not_final", error=RuntimeError("boom"))
    with caplog.at_level(logging.ERROR, logger="error_views"):
        response = logged_client.post(url("invoices_purchases_export_globals"), {})

    assert response.status_code == 200
    assert "invoices_purchases_export_globals" in caplog.text
