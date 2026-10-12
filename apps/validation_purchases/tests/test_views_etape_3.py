"""Tests des vues des étapes 3.1 à 3.6 (familles, franchiseurs, nouveaux clients, abonnements, RFA)"""

import logging
import uuid

import pytest
from django.urls import reverse

from apps.validation_purchases.tests.helpers_views import messages_of
from apps.validation_purchases.views import (
    views_etape_3_1,
    views_etape_3_2,
    views_etape_3_3,
    views_etape_3_5,
    views_etape_3_6,
)

pytestmark = pytest.mark.django_db
HOME = reverse("home")


def url(name, **kwargs):
    return reverse(f"validation_purchases:{name}", kwargs=kwargs or None)


# 3.1 - FAMILLES ===================================================================================
def test_families_invoices_purchases(logged_client, integration_data, make_section):
    rows = integration_data.rows
    rows[0].axe_pro = make_section("PRO", "OPT")
    rows[0].save()

    response = logged_client.get(url("families_invoices_purchases"))

    assert response.status_code == 200
    families = response.context["invoices_famillies"]
    assert [(row["axe_pro"], row["m_00"]) for row in families] == [("", 20), ("OPT", 10)]
    assert families[0]["supplier"] == "WIDEX SAS"
    assert response.context["family_validation"] == integration_data.validation


def test_families_exports(logged_client, stub_excel, caplog):
    stub_excel(views_etape_3_1, "excel_integration_invoices_familly")
    stub_excel(views_etape_3_1, "excel_supplier_details_invoice")

    assert logged_client.get(url("families_invoices_purchases_export"))[
        "Content-Disposition"
    ].startswith("attachment; filename=FACTURES_CONTROLE_FAMILLES_")
    assert logged_client.get(
        url("supplier_details_invoices_purchases_export", third_party_num="FOUR001")
    )["Content-Disposition"].startswith("attachment; filename=FACTURES_CONTROLE_FAMILLES_FOUR001_")

    stub_excel(views_etape_3_1, "excel_integration_invoices_familly", error=RuntimeError("boom"))
    stub_excel(views_etape_3_1, "excel_supplier_details_invoice", error=RuntimeError("boom"))
    with caplog.at_level(logging.ERROR, logger="error_views"):
        first = logged_client.get(url("families_invoices_purchases_export"))
        second = logged_client.get(
            url("supplier_details_invoices_purchases_export", third_party_num="FOUR001")
        )

    assert first.url == url("families_invoices_purchases")
    assert second.url == url("families_invoices_purchases")
    assert "families_invoices_purchases_export" in caplog.text


# 3.1 A - FAMILLES PAR ARTICLES ====================================================================
@pytest.mark.parametrize(
    ("third_party_num", "expected"), [("alls", 1), ("FOUR001", 1), ("INCONNU", 1)]
)
@pytest.mark.usefixtures("integration_data")
def test_articles_families_invoices_purchases(logged_client, third_party_num, expected):
    """La requête des familles ne filtre pas par tiers : même résultat pour tous les paramètres"""
    response = logged_client.get(
        url("articles_families_invoices_purchases", third_party_num=third_party_num)
    )

    assert response.status_code == 200
    assert len(response.context["controles_exports"]) == expected


def test_articles_families_invoices_purchases_export(logged_client):
    response = logged_client.get(url("articles_families_invoices_purchases_export"))

    assert response.status_code == 200
    assert response.context["titre_table"] == "Export Excel"


# VALIDATIONS DES ECRANS 3.x (motif commun) =======================================================
SCREENS = [
    ("families_validation", "families", "familles"),
    ("franchiseurs_validation", "franchiseurs", "CCT/franchiseurs"),
    ("clients_news_validation", "clients_news", "nouveaux clients"),
    ("subscriptions_validation", "subscriptions", "abonnements"),
    ("control_rfa_period_validation", "rfa", "périodes de RFA"),
]


@pytest.mark.parametrize(("name", "flag", "label"), SCREENS)
def test_validations(ajax_client, validation_period, name, flag, label):
    identification = str(validation_period.uuid_identification)

    response = ajax_client.post(url(name), {"uuid_identification": identification, flag: "on"})
    assert response.json() == {"success": "ok"}
    validation_period.refresh_from_db()
    assert getattr(validation_period, flag) is True
    assert f"Le contrôle des {label} est maintenant validé" in messages_of(response)
    assert ajax_client.session["level"] == 20

    response = ajax_client.post(url(name), {"uuid_identification": identification})
    assert response.json() == {"success": "ko"}
    validation_period.refresh_from_db()
    assert getattr(validation_period, flag) is False
    assert f"Le contrôle des {label} est maintenant invalidé" in messages_of(response)
    assert ajax_client.session["level"] == 50


@pytest.mark.parametrize(("name", "flag", "label"), SCREENS)
def test_validations_erreurs(ajax_client, logged_client, name, flag, label, caplog):
    assert ajax_client.get(url(name)).url == HOME
    assert logged_client.post(url(name), {}).url == HOME

    with caplog.at_level(logging.ERROR, logger="error_views"):
        unknown = ajax_client.post(
            url(name), {"uuid_identification": str(uuid.uuid4()), flag: "on"}
        )
        invalid = ajax_client.post(url(name), {flag: "on"})

    assert unknown.json() == {"success": "ko"}
    assert invalid.json() == {"success": "ko"}
    assert "Il y a eu une erreur pendant la validation" in messages_of(unknown)
    assert f"{name} error" in caplog.text
    assert "form invalid" in caplog.text


# ECRANS SIMPLES ET EXPORTS 3.2 / 3.3 / 3.5 ========================================================
@pytest.mark.parametrize(
    ("name", "context_key", "title"),
    [
        ("cct_franchiseurs_purchases", "franchiseurs_validation", "3.2"),
        ("clients_news_purchases", "clients_news_validation", "3.3"),
        ("subscriptions_purchases", "subscriptions_validation", "3.5"),
    ],
)
def test_ecrans_de_controle(logged_client, validation_period, name, context_key, title):
    response = logged_client.get(url(name))

    assert response.status_code == 200
    assert response.context[context_key] == validation_period
    assert response.context["titre_table"].startswith(title)


@pytest.mark.parametrize(
    ("name", "module", "function_name", "prefix", "back"),
    [
        (
            "cct_franchiseurs_purchases_export",
            views_etape_3_2,
            "excel_cct_franchiseurs",
            "CONTROLE_CCT_FFRANCHISEUR_",
            "cct_franchiseurs_purchases",
        ),
        (
            "clients_news_purchases_export",
            views_etape_3_3,
            "excel_clients_news",
            "CONTROLE_NOUVEAUX_CLIENTS_",
            "clients_news_purchases",
        ),
        (
            "subscriptions_purchases_export",
            views_etape_3_5,
            "excel_subscriptions",
            "CONTROLE_ABONNEMENTS_",
            "subscriptions_purchases",
        ),
        (
            "control_rfa_period_export",
            views_etape_3_6,
            "control_rfa_period_excel",
            "CONTROLE_PERIODE_RFA",
            "control_rfa_period",
        ),
    ],
)
def test_exports(logged_client, stub_excel, name, module, function_name, prefix, back, caplog):
    stub_excel(module, function_name)

    response = logged_client.get(url(name))
    assert response["Content-Disposition"].startswith(f"attachment; filename={prefix}")

    stub_excel(module, function_name, error=RuntimeError("boom"))
    with caplog.at_level(logging.ERROR, logger="error_views"):
        response = logged_client.get(url(name))

    assert response.status_code == 302
    assert response.url == url(back)
    assert f"view : {name}" in caplog.text


# 3.6 - PERIODE RFA ================================================================================
def test_control_rfa_period(logged_client, integration_data):
    response = logged_client.get(url("control_rfa_period"))

    assert response.status_code == 200
    rfa = response.context["rfa"]
    assert len(rfa) == 2
    assert rfa[0]["section"] == "RFA01"
    assert rfa[0]["achat_vente"] == "AC"
    assert response.context["rfa_validation"] == integration_data.validation
