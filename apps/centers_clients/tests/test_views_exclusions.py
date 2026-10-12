# pylint: disable=E0401,W0621,R0913
"""
FR : Tests des vues d'exclusions Tiers X3/Maison et Tiers X3/Pays
EN : Tests for supplier/shop and supplier/country exclusion views

created at: 2026-10-10
created by: Paulo ALVES
"""
import logging

import pytest
from django.contrib.messages import get_messages
from django.urls import reverse

from apps.centers_clients.models import MaisonSupllierExclusion, SupllierCountryExclusion
from apps.centers_clients.views import exclusions_tiers_clients_views, exclusions_tiers_pays_clients_views
from apps.core.functions.functions_http_response import CONTENT_TYPE_EXCEL
from apps.core.models import ChangesTrace
from conftest import patched_attrs

pytestmark = pytest.mark.django_db


def _messages(response):
    return [str(message) for message in get_messages(response.wsgi_request)]


# EXCLUSIONS TIERS X3 / MAISON =====================================================================


def test_exclusions_liste(logged_client, make_exclusion):
    """Liste des couples avec son titre"""
    exclusion = make_exclusion()

    response = logged_client.get(reverse("centers_clients:exclusions_list"))

    assert response.status_code == 200
    assert list(response.context["exclusions"]) == [exclusion]
    assert response.context["titre_table"] == "Couples d'exclusion Tiers X3/Client"


def test_exclusion_create(logged_client, make_society, make_maison):
    """GET du formulaire puis création avec message de succès et trace"""
    make_society("FOUR001", is_client=False, in_use=True)
    maison = make_maison("AF0001")
    url = reverse("centers_clients:exclusion_create")

    response = logged_client.get(url)
    assert response.status_code == 200
    assert response.context["titre_table"] == "Création d'un nouveau couple d'exclusion Tiers X3/Client"
    assert response.context["chevron_retour"] == reverse("centers_clients:exclusions_list")

    response = logged_client.post(url, data={"third_party_num": "FOUR001", "cct_uuid_identification": str(maison.uuid_identification)})

    exclusion = MaisonSupllierExclusion.objects.get()
    assert response.status_code == 302
    assert response.url == reverse("centers_clients:exclusions_list")
    assert exclusion.created_by == logged_client.user
    assert _messages(response) == [f"Le couple d'exclusion, {exclusion.third_party_num} - {maison} a été créé avec success"]
    assert ChangesTrace.objects.filter(model_name="maisonsupllierexclusion").count() == 1


def test_exclusion_create_invalide(logged_client):
    """Formulaire vide : réaffiché avec erreurs"""
    response = logged_client.post(reverse("centers_clients:exclusion_create"), data={})

    assert response.status_code == 200
    assert set(response.context["form"].errors) == {"third_party_num", "cct_uuid_identification"}


def test_exclusion_update(logged_client, make_exclusion, make_maison):
    """Modification du couple vers une autre maison"""
    exclusion = make_exclusion()
    other = make_maison("AF0009")
    url = reverse("centers_clients:exclusion_update", kwargs={"pk": exclusion.pk})

    response = logged_client.get(url)
    assert response.status_code == 200
    assert response.context["titre_table"] == "Mise à jour du couple d'exclusion Tiers X3/Client"

    response = logged_client.post(
        url, data={"third_party_num": exclusion.third_party_num.third_party_num, "cct_uuid_identification": str(other.uuid_identification)}
    )

    exclusion.refresh_from_db()
    assert response.status_code == 302
    assert exclusion.cct_uuid_identification == other
    assert exclusion.modified_by == logged_client.user
    assert "a été modifié avec success" in _messages(response)[0]


def test_exclusion_delete(ajax_client, make_exclusion):
    """Suppression ajax : trace puis suppression définitive"""
    exclusion = make_exclusion()

    response = ajax_client.post(reverse("centers_clients:exclusion_delete"), data={"pk": exclusion.pk})

    assert response.json() == {"success": "success"}
    assert not MaisonSupllierExclusion.objects.exists()
    assert ChangesTrace.objects.filter(model_name="maisonsupllierexclusion", action_type=0).count() == 1


def test_exclusion_delete_pk_inconnu(ajax_client, caplog):
    """pk inconnu : ko et erreur journalisée"""
    with caplog.at_level(logging.ERROR, logger="error_views"):
        response = ajax_client.post(reverse("centers_clients:exclusion_delete"), data={"pk": 999})

    assert response.json() == {"success": "ko"}
    assert "exclusion_delete, form invalid" in caplog.text


@pytest.mark.parametrize("method", ["get_ajax", "post_plain"])
def test_exclusion_delete_mauvaise_requete(ajax_client, logged_client, make_exclusion, method):
    """GET ajax ou POST sans ajax : redirection vers l'accueil, rien n'est supprimé"""
    exclusion = make_exclusion()
    url = reverse("centers_clients:exclusion_delete")

    response = ajax_client.get(url) if method == "get_ajax" else logged_client.post(url, data={"pk": exclusion.pk})

    assert response.status_code == 302
    assert response.url == reverse("home")
    assert MaisonSupllierExclusion.objects.filter(pk=exclusion.pk).exists()


def test_exclusion_export(logged_client, make_exclusion):
    """Export xlsx des exclusions"""
    make_exclusion()

    response = logged_client.get(reverse("centers_clients:exclusion_export_list"))

    assert response.status_code == 200
    assert response["Content-Type"] == CONTENT_TYPE_EXCEL
    assert "LISTING_DES_EXCLUSIONS_TIERS_CLIENTS_" in response["Content-Disposition"]


def test_exclusion_export_en_erreur(logged_client, monkeypatch, caplog):
    """Erreur de génération : log et redirection vers la liste"""

    def _boom(*_args, **_kwargs):
        raise RuntimeError("xlsx")

    with patched_attrs(monkeypatch, exclusions_tiers_clients_views, response_file=_boom), caplog.at_level(logging.ERROR, logger="error_views"):
        response = logged_client.get(reverse("centers_clients:exclusion_export_list"))

    assert response.status_code == 302
    assert response.url == reverse("centers_clients:exclusions_list")
    assert "view : exclusion_export_list" in caplog.text


# EXCLUSIONS TIERS X3 / PAYS =======================================================================


def test_exclusions_pays_liste(logged_client, make_country_exclusion):
    """Liste des couples tiers/pays"""
    exclusion = make_country_exclusion()

    response = logged_client.get(reverse("centers_clients:exclusions_country_list"))

    assert response.status_code == 200
    assert list(response.context["exclusions"]) == [exclusion]
    assert response.context["titre_table"] == "Couples d'exclusion Tiers X3/Pays Client"


def test_exclusion_pays_create(logged_client, make_society, make_country):
    """GET puis création d'un couple tiers/pays"""
    make_society("FOUR001", is_client=False, in_use=True)
    make_country("BE", "Belgique")
    url = reverse("centers_clients:exclusion_country_create")

    response = logged_client.get(url)
    assert response.status_code == 200
    assert response.context["titre_table"] == "Création d'un nouveau couple d'exclusion Tiers X3/Pays Clients"

    response = logged_client.post(url, data={"third_party_num": "FOUR001", "pays": "BE"})

    exclusion = SupllierCountryExclusion.objects.get()
    assert response.status_code == 302
    assert response.url == reverse("centers_clients:exclusions_country_list")
    assert exclusion.created_by == logged_client.user
    assert _messages(response) == [f"Le couple d'exclusion, {exclusion.third_party_num} - {exclusion.pays} a été créé avec success"]


def test_exclusion_pays_create_invalide(logged_client):
    """Formulaire vide"""
    response = logged_client.post(reverse("centers_clients:exclusion_country_create"), data={})

    assert response.status_code == 200
    assert set(response.context["form"].errors) == {"third_party_num", "pays"}


def test_exclusion_pays_update(logged_client, make_country_exclusion, make_country):
    """Modification du pays du couple"""
    exclusion = make_country_exclusion()
    make_country("BE", "Belgique")
    url = reverse("centers_clients:exclusion_country_update", kwargs={"pk": exclusion.pk})

    response = logged_client.get(url)
    assert response.status_code == 200
    assert response.context["titre_table"] == "Mise à jour du couple d'exclusion Tiers X3/Pays Clients"

    response = logged_client.post(url, data={"third_party_num": exclusion.third_party_num.third_party_num, "pays": "BE"})

    exclusion.refresh_from_db()
    assert response.status_code == 302
    assert exclusion.pays.country == "BE"
    assert exclusion.modified_by == logged_client.user
    assert "a été modifié avec success" in _messages(response)[0]


def test_exclusion_pays_delete(ajax_client, make_country_exclusion, caplog):
    """Suppression ajax valide puis pk inconnu"""
    exclusion = make_country_exclusion()
    url = reverse("centers_clients:exclusion_country_delete")

    assert ajax_client.post(url, data={"pk": exclusion.pk}).json() == {"success": "success"}
    assert not SupllierCountryExclusion.objects.exists()

    with caplog.at_level(logging.ERROR, logger="error_views"):
        assert ajax_client.post(url, data={"pk": 999}).json() == {"success": "ko"}

    assert "exclusion_country_delete, form invalid" in caplog.text


def test_exclusion_pays_delete_mauvaise_requete(ajax_client, logged_client):
    """GET ajax ou POST sans ajax : redirection"""
    url = reverse("centers_clients:exclusion_country_delete")

    assert ajax_client.get(url).url == reverse("home")
    assert logged_client.post(url, data={"pk": 1}).url == reverse("home")


def test_exclusion_pays_export(logged_client, make_country_exclusion):
    """Export xlsx des exclusions pays"""
    make_country_exclusion()

    response = logged_client.get(reverse("centers_clients:exclusion_country_export_list"))

    assert response.status_code == 200
    assert response["Content-Type"] == CONTENT_TYPE_EXCEL
    assert "LISTING_DES_EXCLUSIONS_TIERS_PAYS_CLIENTS_" in response["Content-Disposition"]


def test_exclusion_pays_export_en_erreur(logged_client, monkeypatch, caplog):
    """Erreur de génération : log et redirection vers la liste des exclusions pays"""

    def _boom(*_args, **_kwargs):
        raise RuntimeError("xlsx")

    with patched_attrs(monkeypatch, exclusions_tiers_pays_clients_views, response_file=_boom), caplog.at_level(logging.ERROR, logger="error_views"):
        response = logged_client.get(reverse("centers_clients:exclusion_country_export_list"))

    assert response.status_code == 302
    assert response.url == reverse("centers_clients:exclusions_country_list")
    assert "view : exclusion_country_export_list" in caplog.text
