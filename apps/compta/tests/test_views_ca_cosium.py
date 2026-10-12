"""Tests des vues ventes / CA Cosium : exports et resets"""

import datetime
import logging

import pytest
from django.urls import reverse

from apps.compta.models import CaClients
from apps.compta.views import ca_cosium_views
from apps.edi.models import EdiImport
from conftest import patched_attrs

pytestmark = pytest.mark.django_db


@pytest.fixture
def period_sales(make_vente, make_maison, month_period):
    """Une vente rattachée et une orpheline dans la période du formulaire"""
    maison = make_maison("AF0001")
    date = datetime.date.fromisoformat(month_period.dte_d) + datetime.timedelta(days=3)
    sale_month = date.replace(day=1)
    make_vente(cct_uuid_identification=maison, date_vente=date, sale_month=sale_month)
    make_vente(code_maison="ORPH", code_cosium="ORPH", date_vente=date, sale_month=sale_month)
    return maison


# EXPORT DES VENTES ================================================================================
@pytest.mark.usefixtures("period_sales")
def test_export_sales_cosium_get(logged_client):
    response = logged_client.get(reverse("compta:export_sales_cosium"))

    assert response.status_code == 200
    assert [row["code_cosium"] for row in response.context["state"]] == ["ORPH"]
    assert response.context["nb_paging"] == 19


@pytest.mark.usefixtures("period_sales")
def test_export_sales_cosium_post(logged_client, month_period):
    response = logged_client.post(
        reverse("compta:export_sales_cosium"), {"periode": month_period.value}
    )

    assert response.status_code == 200
    assert response["Content-Type"].startswith("application/vnd")
    assert "VENTES_COSIUM_" in response["Content-Disposition"]


def test_export_sales_cosium_formulaire_invalide(logged_client, caplog):
    with caplog.at_level(logging.ERROR, logger="error_views"):
        response = logged_client.post(reverse("compta:export_sales_cosium"), {"periode": "x"})

    assert response.status_code == 200
    assert "erreur form" in caplog.text


def test_export_sales_cosium_exception(logged_client, month_period, monkeypatch, caplog):
    def boom(*args, **kwargs):
        raise RuntimeError("boom")

    with (
        patched_attrs(monkeypatch, ca_cosium_views, response_file=boom),
        caplog.at_level(logging.ERROR, logger="error_views"),
    ):
        response = logged_client.post(
            reverse("compta:export_sales_cosium"), {"periode": month_period.value}
        )

    assert response.status_code == 200
    assert "erreur export_sales_cosium" in caplog.text


# EXPORT DU CA =====================================================================================
def test_export_ca_cosium_get(logged_client):
    response = logged_client.get(reverse("compta:export_ca_cosium"))

    assert response.status_code == 200
    assert response.context["state"] is False
    assert response.context["message_ca"] == ""


def test_export_ca_cosium_post_sans_ca(logged_client, month_period):
    response = logged_client.post(
        reverse("compta:export_ca_cosium"), {"periode": month_period.value}
    )

    assert response.status_code == 200
    assert "semble ne pas avoir été importé" in response.context["message_ca"]


def test_export_ca_cosium_post_avec_ca(logged_client, make_ca_client, month_period):
    make_ca_client(date_ca=month_period.dte_f)
    response = logged_client.post(
        reverse("compta:export_ca_cosium"), {"periode": month_period.value}
    )

    assert "CA_PAR_MAISONS_FAMILLES_" in response["Content-Disposition"]


def test_export_ca_cosium_formulaire_invalide_et_exception(
    logged_client, month_period, monkeypatch, caplog
):
    with caplog.at_level(logging.ERROR, logger="error_views"):
        logged_client.post(reverse("compta:export_ca_cosium"), {"periode": "x"})

    assert "erreur form" in caplog.text

    def boom(*args, **kwargs):
        raise RuntimeError("boom")

    with (
        patched_attrs(monkeypatch, ca_cosium_views.CaClients.objects, filter=boom),
        caplog.at_level(logging.ERROR, logger="error_views"),
    ):
        response = logged_client.post(
            reverse("compta:export_ca_cosium"), {"periode": month_period.value}
        )

    assert response.status_code == 200
    assert "erreur export_ca_cosium" in caplog.text


# RESETS ===========================================================================================
def test_reset_clients_in_sales(logged_client, make_vente, make_maison):
    maison = make_maison("AF0005", code_maison="AF0005")
    vente = make_vente(code_maison="AF0005")

    response = logged_client.get(reverse("compta:reset_clients_in_sales"))

    assert response.status_code == 302
    assert response.url == reverse("compta:export_sales_cosium")
    vente.refresh_from_db()
    assert vente.cct_uuid_identification == maison
    assert logged_client.session["level"] == 20


def test_reset_clients_in_sales_erreur(logged_client, monkeypatch, caplog):
    def boom(cursor):
        raise RuntimeError("boom")

    with (
        patched_attrs(monkeypatch, ca_cosium_views, set_cct_ventes=boom),
        caplog.at_level(logging.ERROR),
    ):
        response = logged_client.get(reverse("compta:reset_clients_in_sales"))

    assert response.status_code == 302
    assert logged_client.session["level"] == 50
    assert "erreur reset_clients_in_sales" in caplog.text


@pytest.fixture
def subscriptions_in_period(make_edi_import, month_period):
    date = datetime.date.fromisoformat(month_period.dte_d) + datetime.timedelta(days=5)
    make_edi_import(flow_name="ROYALTIES", invoice_date=date)
    make_edi_import(flow_name="Widex", invoice_date=date, reference_article="W1")
    return date


def test_reset_exhange_rates_in_sales_get(logged_client):
    response = logged_client.get(reverse("compta:reset_exhange_rates_in_sales"))

    assert response.status_code == 200
    assert "taux de change" in response.context["titre_table"]


@pytest.mark.usefixtures("subscriptions_in_period")
def test_reset_exhange_rates_in_sales_post(logged_client, month_period, monkeypatch):
    calls = []
    with patched_attrs(
        monkeypatch,
        ca_cosium_views,
        update_exchange_rates=lambda d, f: calls.append(("rates", d, f)),
        set_ca=lambda d, f, user: calls.append(("ca", d, f, user)),
    ):
        response = logged_client.post(
            reverse("compta:reset_exhange_rates_in_sales"), {"periode": month_period.value}
        )

    assert response.status_code == 302
    assert calls == [
        ("rates", month_period.dte_d, month_period.dte_f),
        ("ca", month_period.dte_d, month_period.dte_f, logged_client.user.uuid_identification),
    ]
    assert list(EdiImport.objects.values_list("flow_name", flat=True)) == ["Widex"]
    assert logged_client.session["level"] == 20


@pytest.mark.parametrize(
    "url_name", ["compta:reset_exhange_rates_in_sales", "compta:reset_sales", "compta:reset_ca"]
)
def test_resets_formulaire_invalide(logged_client, url_name, caplog):
    with caplog.at_level(logging.ERROR, logger="error_views"):
        response = logged_client.post(reverse(url_name), {"periode": "x"})

    assert response.status_code == 200
    assert logged_client.session["level"] == 50
    assert "erreur form" in caplog.text


@pytest.mark.usefixtures("subscriptions_in_period")
def test_reset_sales(logged_client, month_period, monkeypatch):
    calls = []
    with patched_attrs(
        monkeypatch,
        ca_cosium_views,
        force_update_sales=lambda d, f: calls.append("force"),
        set_ca=lambda d, f, user: calls.append("ca"),
    ):
        response = logged_client.post(
            reverse("compta:reset_sales"), {"periode": month_period.value}
        )

    assert response.status_code == 302
    assert response.url == reverse("compta:export_sales_cosium")
    assert calls == ["force", "ca"]
    assert list(EdiImport.objects.values_list("flow_name", flat=True)) == ["Widex"]


def test_reset_sales_get(logged_client):
    response = logged_client.get(reverse("compta:reset_sales"))

    assert response.status_code == 200
    assert response.context["titre_table"] == "Reset des ventes Cosium"


@pytest.mark.usefixtures("subscriptions_in_period")
def test_reset_ca(logged_client, month_period, make_ca_client, monkeypatch):
    make_ca_client(date_ca=month_period.dte_f)
    calls = []
    with patched_attrs(
        monkeypatch,
        ca_cosium_views,
        update_exchange_rates=lambda d, f: calls.append("rates"),
        set_ca=lambda d, f, user: calls.append("ca"),
    ):
        response = logged_client.post(reverse("compta:reset_ca"), {"periode": month_period.value})

    assert response.status_code == 302
    assert response.url == reverse("compta:export_ca_cosium")
    assert calls == ["rates", "ca"]
    assert CaClients.objects.count() == 0
    assert list(EdiImport.objects.values_list("flow_name", flat=True)) == ["Widex"]


def test_reset_ca_get(logged_client):
    response = logged_client.get(reverse("compta:reset_ca"))

    assert response.status_code == 200
    assert "Chiffre d'affaires" in response.context["titre_table"]
