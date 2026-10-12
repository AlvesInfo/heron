# pylint: disable=E0401,W0621
"""
FR : Tests des vues API des dropdowns semantic (apps/core/views/views.py), consommatrices de
     l'API TVA et comptes de apps.accountancy
EN : Tests for semantic dropdown API views, consumers of accountancy VAT/accounts API

Commentaire:

L'URLconf complète du projet est utilisée (données de référence edi chargées par le conftest
racine) ; reverse() n'est appelé qu'à l'intérieur des tests, jamais à la collecte.

created at: 2026-10-10
created by: Paulo ALVES
"""
import logging

import pytest
from django.urls import reverse

from apps.accountancy.bin.api_get_models_accountacy import get_vat
from apps.core.views import views as core_views
from conftest import patched_attrs

pytestmark = pytest.mark.django_db


def _url(models, query, third_party_num=None):
    if third_party_num is None:
        return reverse("core:api_models_query", kwargs={"models": models, "query": query})

    return reverse(
        "core:api_models_query_third_party_num",
        kwargs={"models": models, "third_party_num": third_party_num, "query": query},
    )


def _payload(response):
    assert response["Content-Type"] == "application/json"
    return response.json()


# ROUTAGE ==========================================================================================


def test_routes():
    """Les deux routes sont exposées sous /core/ avec le bon nombre de segments"""
    assert _url("vats", "fra") == "/core/api_models_query/vats/fra/"
    assert _url("vats", "fra", "BBGR001") == "/core/api_models_query/vats/BBGR001/fra/"


def test_model_dict_branche_l_api_accountancy():
    """Les clés vats / vats_alls / accounts pointent sur les fonctions d'accountancy et core"""
    assert core_views.MODEL_DICT["vats"] is get_vat
    assert core_views.MODEL_DICT["vats_alls"].__module__ == "apps.accountancy.bin.api_get_models_accountacy"
    assert core_views.MODEL_DICT["accounts"].__module__ == "apps.core.bin.api_get_models"


# ACCÈS ============================================================================================


ROUTE_ARGS = [("vats", "fra"), ("vats", "fra", "BBGR001")]


@pytest.mark.parametrize("route_args", ROUTE_ARGS)
def test_non_authentifie_redirige_vers_le_login(client, route_args):
    """Le LoginMiddleware renvoie les anonymes vers la page de login"""
    response = client.get(_url(*route_args), HTTP_X_REQUESTED_WITH="XMLHttpRequest")

    assert response.status_code == 302
    assert response.url == reverse("accounts:login")


@pytest.mark.parametrize("route_args", ROUTE_ARGS)
def test_requete_non_ajax_redirige_vers_home(logged_client, route_args):
    """Sans en-tête X-Requested-With, la vue redirige vers l'accueil"""
    response = logged_client.get(_url(*route_args))

    assert response.status_code == 302
    assert response.url == reverse("home")


@pytest.mark.parametrize("route_args", ROUTE_ARGS)
def test_requete_ajax_post_redirige_vers_home(ajax_client, route_args):
    """Seul le GET est accepté, même en ajax"""
    response = ajax_client.post(_url(*route_args))

    assert response.status_code == 302
    assert response.url == reverse("home")


# API TVA (accountancy) ============================================================================


def test_vats_renvoie_les_taxes_filtrees(ajax_client, make_vat):
    """Recherche insensible à la casse sur 'tva|régime', format {pk, model} des dropdowns"""
    make_vat("001", "FRA")
    make_vat("002", "FRA")
    make_vat("011", "INT")

    response = ajax_client.get(_url("vats", "FRA"))

    assert response.status_code == 200
    assert _payload(response) == {
        "success": [{"pk": "001", "model": "001 - FRA"}, {"pk": "002", "model": "002 - FRA"}]
    }


def test_vats_sans_resultat(ajax_client, make_vat):
    """Aucune correspondance : liste vide, pas 'ko'"""
    make_vat("001", "FRA")

    assert _payload(ajax_client.get(_url("vats", "zzz"))) == {"success": []}


@pytest.mark.parametrize(("query", "expected_pks"), [("FR'A", ["001", "002"]), ("100%", []), ("1|F", ["001"])])
def test_vats_nettoyage_de_la_requete(ajax_client, make_vat, query, expected_pks):
    """Les apostrophes sont retirées, le % est échappé (donc littéral), le texte passé en minuscule"""
    make_vat("001", "FRA")
    make_vat("002", "FRA")

    payload = _payload(ajax_client.get(_url("vats", query)))

    assert [row["pk"] for row in payload["success"]] == expected_pks


def test_vats_alls_renvoie_toutes_les_taxes(ajax_client, make_vat, caplog):
    """Les clés *_alls ignorent le texte de recherche et renvoient tous les enregistrements"""
    make_vat("001", "FRA")
    make_vat("011", "INT")

    with caplog.at_level(logging.ERROR, logger="error_views"):
        payload = _payload(ajax_client.get(_url("vats_alls", "zzz")))

    assert payload == {"success": [{"pk": "001", "model": "001 - FRA"}, {"pk": "011", "model": "011 - INT"}]}
    assert caplog.text == ""


def test_alls_avec_tiers_passe_le_tiers_seul(ajax_client, make_vat, monkeypatch):
    """Avec tiers, une clé *_alls reçoit uniquement le tiers (ex. get_articles_alls(third_party_num))"""
    make_vat("001", "FRA")
    received = []

    def _alls(third_party_num):
        received.append(third_party_num)
        return core_views.MODEL_DICT["vats_alls"]()

    with patched_attrs(monkeypatch, core_views, MODEL_DICT={**core_views.MODEL_DICT, "vats_tiers_alls": _alls}):
        payload = _payload(ajax_client.get(_url("vats_tiers_alls", "zzz", "BBGR001")))

    assert received == ["BBGR001"]
    assert payload == {"success": [{"pk": "001", "model": "001 - FRA"}]}


def test_accounts_renvoie_les_comptes_sage(ajax_client, make_account):
    """La clé accounts interroge AccountSage (pk = uuid sérialisé en texte)"""
    account = make_account("FRA", "411000")
    make_account("FRA", "607000")

    payload = _payload(ajax_client.get(_url("accounts", "411")))

    assert payload == {"success": [{"pk": str(account.uuid_identification), "model": "411000 - FRA"}]}


def test_modele_inconnu(ajax_client, caplog):
    """Un modèle absent de MODEL_DICT renvoie 'ko' sans journaliser d'erreur"""
    with caplog.at_level(logging.ERROR, logger="error_views"):
        response = ajax_client.get(_url("inconnu", "fra"))

    assert response.status_code == 200
    assert _payload(response) == {"success": "ko"}
    assert caplog.text == ""


# API AVEC TIERS ===================================================================================


def test_third_party_num_succes(ajax_client, make_vat, monkeypatch):
    """La variante avec tiers passe (requête, tiers) à la fonction du MODEL_DICT"""
    make_vat("001", "FRA")
    received = {}

    def _vats_for_third_party(str_query, third_party_num):
        received.update({"query": str_query, "third_party_num": third_party_num})
        return get_vat(str_query)

    with patched_attrs(
        monkeypatch, core_views, MODEL_DICT={**core_views.MODEL_DICT, "vats_tiers": _vats_for_third_party}
    ):
        payload = _payload(ajax_client.get(_url("vats_tiers", "FR'A", "BBGR001")))

    assert received == {"query": "fra", "third_party_num": "BBGR001"}
    assert payload == {"success": [{"pk": "001", "model": "001 - FRA"}]}


def test_third_party_num_fonction_a_un_seul_argument(ajax_client, make_vat, caplog):
    """get_vat n'accepte pas le tiers : TypeError avalée, réponse 'ko' journalisée"""
    make_vat("001", "FRA")

    with caplog.at_level(logging.ERROR, logger="error_views"):
        response = ajax_client.get(_url("vats", "fra", "BBGR001"))

    assert _payload(response) == {"success": "ko"}
    assert "view : article_rest_api_query" in caplog.text


def test_third_party_num_modele_inconnu(ajax_client):
    """Modèle inconnu avec tiers : 'ko'"""
    assert _payload(ajax_client.get(_url("inconnu", "fra", "BBGR001"))) == {"success": "ko"}
