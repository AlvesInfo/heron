# pylint: disable=E0401,W0621,R0913
"""
FR : Tests des vues des abonnements par maison et des familles clients
EN : Tests for subscriptions and client families views

created at: 2026-10-10
created by: Paulo ALVES
"""
import logging
from decimal import Decimal

import pytest
from django.contrib.messages import get_messages
from django.urls import reverse

from apps.centers_clients.models import ClientFamilly, MaisonSubcription
from apps.centers_clients.views import clients_familly_views, maisons_subscriptions
from apps.core.functions.functions_http_response import CONTENT_TYPE_EXCEL
from apps.core.models import ChangesTrace
from conftest import patched_attrs

pytestmark = pytest.mark.django_db


def _messages(response):
    return [str(message) for message in get_messages(response.wsgi_request)]


# ABONNEMENTS ======================================================================================


def test_abonnements_liste(logged_client, make_subscription):
    """Liste values() des abonnements"""
    subscription = make_subscription()

    response = logged_client.get(reverse("centers_clients:subscriptions_list"))

    rows = list(response.context["subscriptions"])
    assert response.status_code == 200
    assert rows[0]["pk"] == subscription.pk
    assert rows[0]["article__reference"] == subscription.article.reference
    assert response.context["titre_table"] == "Abonnements"


@pytest.fixture
def subscription_post_data(make_maison, make_article, make_unit, make_invoice_function, make_signboard, make_vat):
    """Données POST valides d'un abonnement"""
    make_maison("AF0001")
    article = make_article("ABO-1")
    make_unit(1, "U")
    make_invoice_function("ABONNEMENT")
    make_signboard("ACF")
    make_vat("001")
    return {
        "maison": "AF0001",
        "article": str(article.uuid_identification),
        "qty": "2",
        "unit_weight": "1",
        "net_unit_price": "99.90",
        "function": "ABONNEMENT",
        "for_signboard": "ACF",
        "vat": "001",
    }


def test_abonnement_create(logged_client, subscription_post_data):
    """GET puis création avec message et redirection vers la liste (get_absolute_url du modèle)"""
    url = reverse("centers_clients:subscription_create")

    response = logged_client.get(url)
    assert response.status_code == 200
    assert response.context["create"] is True
    assert response.context["titre_table"] == "Création d'un nouvel Abonnement"

    response = logged_client.post(url, data=subscription_post_data)

    subscription = MaisonSubcription.objects.get()
    assert response.status_code == 302
    assert response.url == reverse("centers_clients:subscriptions_list")
    assert subscription.created_by == logged_client.user
    assert subscription.qty == Decimal("2")
    assert "a été créé avec success" in _messages(response)[0]


def test_abonnement_create_invalide(logged_client, subscription_post_data):
    """Sans article : erreurs"""
    response = logged_client.post(reverse("centers_clients:subscription_create"), data={**subscription_post_data, "article": ""})

    assert response.status_code == 200
    assert "article" in response.context["form"].errors


def test_abonnement_update(logged_client, make_subscription, subscription_post_data):
    """Modification de la quantité"""
    subscription = make_subscription()
    url = reverse("centers_clients:subscription_update", kwargs={"pk": subscription.pk})

    response = logged_client.get(url)
    assert response.status_code == 200
    assert response.context["titre_table"] == "Mise à jour d'un Abonnement"
    assert response.context["chevron_retour"] == reverse("centers_clients:subscriptions_list")

    response = logged_client.post(url, data={**subscription_post_data, "qty": "5"})

    subscription.refresh_from_db()
    assert response.status_code == 302
    assert subscription.qty == Decimal("5")
    assert subscription.modified_by == logged_client.user
    assert ChangesTrace.objects.filter(model_name="maisonsubcription", action_type=2).count() == 1


def test_abonnement_delete(ajax_client, logged_client, make_subscription, caplog):
    """Suppression ajax, pk inconnu, mauvaises requêtes"""
    subscription = make_subscription()
    url = reverse("centers_clients:subscription_delete")

    assert ajax_client.get(url).url == reverse("home")
    assert logged_client.post(url, data={"pk": subscription.pk}).url == reverse("home")
    assert MaisonSubcription.objects.exists()

    assert ajax_client.post(url, data={"pk": subscription.pk}).json() == {"success": "success"}
    assert not MaisonSubcription.objects.exists()

    with caplog.at_level(logging.ERROR, logger="error_views"):
        assert ajax_client.post(url, data={"pk": subscription.pk}).json() == {"success": "ko"}

    assert "subscription_delete, form invalid" in caplog.text


def test_abonnements_export(logged_client, make_subscription, monkeypatch, caplog):
    """Export xlsx puis chemin d'erreur"""
    make_subscription()

    response = logged_client.get(reverse("centers_clients:subscriptions_export_list"))
    assert response.status_code == 200
    assert response["Content-Type"] == CONTENT_TYPE_EXCEL
    assert "LISTING_DES_ABONNEMENTS_" in response["Content-Disposition"]

    def _boom(*_args, **_kwargs):
        raise RuntimeError("xlsx")

    with patched_attrs(monkeypatch, maisons_subscriptions, response_file=_boom), caplog.at_level(logging.ERROR, logger="error_views"):
        response = logged_client.get(reverse("centers_clients:subscriptions_export_list"))

    assert response.status_code == 302
    assert response.url == reverse("centers_clients:subscriptions_list")
    assert "view : subscriptions_export_list" in caplog.text


def test_insert_or_update_subscriptions(logged_client, monkeypatch):
    """GET affiche l'écran, POST lance l'import et affiche ses messages"""
    url = reverse("centers_clients:insert_or_update_subscriptions")

    response = logged_client.get(url)
    assert response.status_code == 200
    assert response.context["titre_table"] == "Import ou Mise à Jour des abonnement par maisons"
    assert response.context["messages_errors"] == ""
    assert response.context["messages_ok"] == ""

    with patched_attrs(monkeypatch, maisons_subscriptions, import_abonnements_par_maisons=lambda: ("erreur X", "fichier OK")):
        response = logged_client.post(url)

    assert response.status_code == 200
    assert response.context["messages_errors"] == "erreur X"
    assert response.context["messages_ok"] == "fichier OK"


# FAMILLES CLIENTS =================================================================================


def test_familles_liste(logged_client, make_client_familly):
    """Liste des familles"""
    familly = make_client_familly("franchise")

    response = logged_client.get(reverse("centers_clients:client_familly_list"))

    assert response.status_code == 200
    assert list(response.context["famillies"]) == [familly]
    assert response.context["titre_table"] == "Catégories Clients"


def test_famille_create(logged_client):
    """GET puis création (nom capitalisé) avec message et redirection"""
    url = reverse("centers_clients:client_familly_create")

    response = logged_client.get(url)
    assert response.status_code == 200
    assert response.context["titre_table"] == "Création d'une nouvelle Catégorie Client"
    assert response.context["chevron_retour"] == reverse("centers_clients:client_familly_list")

    response = logged_client.post(url, data={"name": "succursale", "comment": "intégrées"})

    familly = ClientFamilly.objects.get()
    assert response.status_code == 302
    assert response.url == reverse("centers_clients:client_familly_list")
    assert familly.name == "Succursale"
    assert familly.created_by == logged_client.user
    assert _messages(response) == ["La catégorie succursale, a été créé avec success"]


def test_famille_create_invalide(logged_client, make_client_familly):
    """Nom en doublon (même en minuscules) : formulaire réaffiché, pas d'IntegrityError"""
    make_client_familly("franchise")

    response = logged_client.post(reverse("centers_clients:client_familly_create"), data={"name": "franchise"})

    assert response.status_code == 200
    assert "name" in response.context["form"].errors


def test_famille_update(logged_client, make_client_familly):
    """Modification du commentaire"""
    familly = make_client_familly("franchise")
    url = reverse("centers_clients:client_familly_update", kwargs={"pk": familly.pk})

    response = logged_client.get(url)
    assert response.status_code == 200
    assert response.context["titre_table"] == "Mise à jour d'une Catégorie Client"

    response = logged_client.post(url, data={"name": "Franchise", "comment": "Nouveau commentaire"})

    familly.refresh_from_db()
    assert response.status_code == 302
    assert familly.comment == "Nouveau commentaire"
    assert familly.modified_by == logged_client.user
    assert _messages(response) == ["La catégorie Franchise, a été modifiée avec success"]


def test_famille_delete(ajax_client, logged_client, make_client_familly, caplog):
    """Suppression ajax, pk inconnu, mauvaises requêtes"""
    familly = make_client_familly("franchise")
    url = reverse("centers_clients:client_familly_delete")

    assert ajax_client.get(url).url == reverse("home")
    assert logged_client.post(url, data={"pk": familly.pk}).url == reverse("home")

    assert ajax_client.post(url, data={"pk": familly.pk}).json() == {"success": "success"}
    assert not ClientFamilly.objects.exists()

    with caplog.at_level(logging.ERROR, logger="error_views"):
        assert ajax_client.post(url, data={"pk": familly.pk}).json() == {"success": "ko"}

    assert "client_familly_delete, form invalid" in caplog.text


def test_famille_export(logged_client, make_client_familly, monkeypatch, caplog):
    """Export xlsx puis chemin d'erreur"""
    make_client_familly("franchise")

    response = logged_client.get(reverse("centers_clients:export_client_familly_list"))
    assert response.status_code == 200
    assert response["Content-Type"] == CONTENT_TYPE_EXCEL
    assert "LISTING_DES_CATEGORIES_CLIENTS_" in response["Content-Disposition"]

    def _boom(*_args, **_kwargs):
        raise RuntimeError("xlsx")

    with patched_attrs(monkeypatch, clients_familly_views, response_file=_boom), caplog.at_level(logging.ERROR, logger="error_views"):
        response = logged_client.get(reverse("centers_clients:export_client_familly_list"))

    assert response.status_code == 302
    assert response.url == reverse("centers_clients:client_familly_list")
    assert "view : export_client_familly_list" in caplog.text
