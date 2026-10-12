"""Tests des vues des dictionnaires Entêtes / Axe Pro des détails de facturation"""
import logging

import pytest
from django.urls import reverse

from apps.core.models import ChangesTrace
from apps.invoices.models import AxesDetails, EnteteDetails
from apps.invoices.views import axes_details_views
from conftest import patched_attrs

pytestmark = pytest.mark.django_db


# ENTÊTES ==========================================================================================
def test_entetes_list(logged_client, make_entete_details):
    make_entete_details("Montures")
    response = logged_client.get(reverse("invoices:entete_details_list"))

    assert response.status_code == 200
    assert [row.column_name for row in response.context["entetes_details"]] == ["Montures"]


def test_entetes_create(logged_client):
    url = reverse("invoices:entete_details_create")
    assert logged_client.get(url).context["titre_table"].startswith("Création")

    response = logged_client.post(url, {"ranking": 2, "column_name": "Verres"})

    assert response.status_code == 302
    assert response.url == reverse("invoices:entete_details_list")
    entete = EnteteDetails.objects.get(column_name="Verres")
    assert entete.created_by == logged_client.user
    assert ChangesTrace.objects.filter(model_name="entetedetails").exists()
    assert logged_client.session["level"] == 20


def test_entetes_update(logged_client, make_entete_details):
    entete = make_entete_details("Montures")
    url = reverse("invoices:entete_details_update", kwargs={"pk": entete.pk})
    assert logged_client.get(url).context["titre_table"].startswith("Mise à jour")

    response = logged_client.post(url, {"ranking": 9, "column_name": "Montures"})

    assert response.status_code == 302
    entete.refresh_from_db()
    assert entete.ranking == 9
    assert entete.modified_by == logged_client.user


def test_entetes_delete(ajax_client, make_entete_details, caplog):
    entete = make_entete_details("Montures")
    url = reverse("invoices:entete_details_delete")

    assert ajax_client.post(url, {"pk": entete.pk}).json() == {"success": "success"}
    assert not EnteteDetails.objects.filter(pk=entete.pk).exists()

    with caplog.at_level(logging.ERROR):
        assert ajax_client.post(url, {"pk": 999999}).json() == {"success": "ko"}

    assert "form invalid" in caplog.text


def test_entetes_delete_refuse_hors_ajax_ou_get(logged_client, ajax_client, make_entete_details):
    """Un POST sans X-Requested-With ou un GET ajax sont redirigés vers l'accueil"""
    entete = make_entete_details("Montures")
    url = reverse("invoices:entete_details_delete")

    assert logged_client.post(url, {"pk": entete.pk}).url == reverse("home")
    assert ajax_client.get(url).url == reverse("home")
    assert EnteteDetails.objects.filter(pk=entete.pk).exists()


def test_entetes_export(logged_client, make_entete_details, monkeypatch, caplog):
    make_entete_details("Montures")
    response = logged_client.get(reverse("invoices:entete_details_export_list"))

    assert "LISTING_DES_ENTETES_DETAILS" in response["Content-Disposition"]

    def boom(*args, **kwargs):
        raise RuntimeError("boom")

    with patched_attrs(monkeypatch, axes_details_views, response_file=boom), caplog.at_level(logging.ERROR):
        response = logged_client.get(reverse("invoices:entete_details_export_list"))

    assert response.url == reverse("invoices:entete_details_list")
    assert "entetes_details_export_list" in caplog.text


# AXES =============================================================================================
def test_axes_list(logged_client, make_axes_details):
    make_axes_details("OPT", "Montures")
    response = logged_client.get(reverse("invoices:axes_details_list"))

    assert response.status_code == 200
    assert [row.column_name.column_name for row in response.context["axes_details"]] == ["Montures"]


def test_axes_create(logged_client, make_section, make_entete_details):
    section = make_section("PRO", "AUD")
    entete = make_entete_details("Audio")
    url = reverse("invoices:axes_details_create")
    assert logged_client.get(url).context["titre_table"].startswith("Création")

    response = logged_client.post(url, {"axe_pro": section.uuid_identification, "column_name": entete.column_name})

    assert response.status_code == 302
    assert response.url == reverse("invoices:axes_details_list")
    axe = AxesDetails.objects.get(axe_pro=section)
    assert axe.created_by == logged_client.user
    assert axe.column_name == entete


def test_axes_update(logged_client, make_axes_details, make_entete_details):
    axe = make_axes_details("OPT", "Montures")
    autre = make_entete_details("Verres")
    url = reverse("invoices:axes_details_update", kwargs={"pk": axe.pk})
    assert logged_client.get(url).context["titre_table"].startswith("Mise à jour")

    response = logged_client.post(url, {"axe_pro": axe.axe_pro.uuid_identification, "column_name": autre.column_name})

    assert response.status_code == 302
    axe.refresh_from_db()
    assert axe.column_name == autre
    assert axe.modified_by == logged_client.user


def test_axes_delete(ajax_client, logged_client, make_axes_details, caplog):
    axe = make_axes_details()
    url = reverse("invoices:axes_details_delete")

    assert logged_client.post(url, {"pk": axe.pk}).url == reverse("home")
    assert ajax_client.post(url, {"pk": axe.pk}).json() == {"success": "success"}
    assert not AxesDetails.objects.filter(pk=axe.pk).exists()

    with caplog.at_level(logging.ERROR):
        assert ajax_client.post(url, {"pk": 999999}).json() == {"success": "ko"}

    assert "axes_details_delete, form invalid" in caplog.text


def test_axes_export(logged_client, make_axes_details, monkeypatch, caplog):
    make_axes_details()
    response = logged_client.get(reverse("invoices:axes_details_export_list"))

    assert "LISTING_DES_AXE_PRO_DETAILS" in response["Content-Disposition"]

    def boom(*args, **kwargs):
        raise RuntimeError("boom")

    with patched_attrs(monkeypatch, axes_details_views, response_file=boom), caplog.at_level(logging.ERROR):
        response = logged_client.get(reverse("invoices:axes_details_export_list"))

    assert response.url == reverse("invoices:axes_details_list")
