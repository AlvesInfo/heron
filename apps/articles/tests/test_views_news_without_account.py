# pylint: disable=E0401,W0621,R0913
"""FR : Tests des vues des nouveaux articles (étape 1.1) et des articles sans comptes (étape 1.2)


EN : Tests for new articles and articles without account views

created at: 2026-10-10
created by: Paulo ALVES
"""

import logging

import pytest
from django.contrib.messages import get_messages
from django.urls import reverse

from apps.articles.models import Article, ArticleAccount
from apps.articles.views import (
    views_articles_news_etape_1_1,
    views_articles_with_no_account_etape_1_2,
)
from apps.core.functions.functions_http_response import CONTENT_TYPE_EXCEL
from apps.core.models import ChangesTrace
from conftest import patched_attrs

pytestmark = pytest.mark.django_db


def _messages(response):
    return [str(message) for message in get_messages(response.wsgi_request)]


@pytest.fixture
def complet(make_article, make_society, make_big_category, default_sections):
    """Un article complet (tous axes + catégorie) flagué nouveau, un article sans axe pro"""
    four = make_society("FOUR001", is_client=False)
    category = make_big_category("Marchandises")
    return {
        "nouveau": make_article(
            "NEW-1",
            society=four,
            big_category=category,
            axe_pro=default_sections["PRO"],
            new_article=True,
        ),
        "sans_pro": make_article(
            "SANS-PRO", society=four, big_category=category, new_article=False
        ),
        "ok": make_article(
            "OK-1",
            society=four,
            big_category=category,
            axe_pro=default_sections["PRO"],
            new_article=False,
        ),
    }


# NOUVEAUX ARTICLES ================================================================================


def test_liste_nouveaux_articles(logged_client, complet, make_edi_import, make_default_axes):
    """Les lignes EDI inconnues deviennent des articles nouveaux, la liste montre nouveaux et incomplets"""
    make_default_axes()
    make_edi_import("FOUR001", "EDI-NEW", axe_pro=complet["nouveau"].axe_pro)

    response = logged_client.get(reverse("articles:new_articles_list"))

    references = {row["reference"] for row in response.context["articles"]}
    assert response.status_code == 200
    assert references == {"NEW-1", "SANS-PRO", "EDI-NEW"}
    assert Article.objects.get(reference="EDI-NEW").new_article is True
    assert response.context["titre_table"] == "1.1 - Liste des Nouveaux Articles"
    assert response.context["url_validation"] == reverse("articles:articles_new_validation")
    assert (
        logged_client.get(reverse("articles:new_articles_list"), {"page": "99"})
        .context["articles"]
        .number
        == 1
    )
    assert (
        logged_client.get(reverse("articles:new_articles_list"), {"page": "x"})
        .context["articles"]
        .number
        == 1
    )


def test_validation_nouveaux_articles_tous(logged_client, complet):
    """POST : les nouveaux articles complets sont validés, message de succès, trace"""
    Article.objects.filter(reference="SANS-PRO").update(
        axe_pro=complet["nouveau"].axe_pro, new_article=True
    )

    response = logged_client.post(reverse("articles:articles_new_validation"))

    assert response.json() == {"success": "ok"}
    assert not Article.objects.filter(new_article=True).exists()
    assert _messages(response) == ["Tous les articles ont étés mis à jour (2)"]
    assert ChangesTrace.objects.filter(model_name="article").count() == 1


@pytest.mark.usefixtures("complet")
def test_validation_nouveaux_articles_partielle(logged_client):
    """Un article incomplet reste : message d'avertissement, trace quand même"""
    response = logged_client.post(reverse("articles:articles_new_validation"))

    nouveau = Article.objects.get(reference="NEW-1")
    assert nouveau.new_article is False
    assert nouveau.modified_by == logged_client.user
    assert _messages(response) == [
        "Il reste des articles qui comporte des erreus. Articles mis à jour : 1 / 2"
    ]
    assert ChangesTrace.objects.filter(model_name="article").count() == 1


@pytest.mark.usefixtures("complet")
def test_validation_nouveaux_articles_aucune_mise_a_jour(logged_client):
    """Rien de validable : message sans trace"""
    Article.objects.filter(reference="NEW-1").update(new_article=False)

    response = logged_client.post(reverse("articles:articles_new_validation"))

    assert _messages(response) == [
        "Il reste des articles qui comporte des erreus. Articles mis à jour : 0 / 1"
    ]
    assert not ChangesTrace.objects.filter(model_name="article").exists()


def test_validation_nouveaux_articles_get_ou_vide(logged_client):
    """GET ou aucun article : réponse ok sans message"""
    response = logged_client.get(reverse("articles:articles_new_validation"))

    assert response.json() == {"success": "ok"}
    assert _messages(response) == []


@pytest.mark.usefixtures("complet")
def test_export_nouveaux_articles(logged_client, monkeypatch, caplog):
    """Export xlsx puis chemin d'erreur"""
    url = reverse("articles:articles_news_export_list")

    response = logged_client.get(url)
    assert response.status_code == 200
    assert response["Content-Type"] == CONTENT_TYPE_EXCEL
    assert "LISTING_DES_NOUVEAUX_ARTICLES_" in response["Content-Disposition"]

    def _boom(*_args, **_kwargs):
        raise RuntimeError("xlsx")

    with (
        patched_attrs(monkeypatch, views_articles_news_etape_1_1, response_file=_boom),
        caplog.at_level(logging.ERROR, logger="export_excel"),
    ):
        response = logged_client.get(url)

    assert response.status_code == 302
    assert response.url == reverse("articles:new_articles_list")
    assert "view : articles_news_export_list" in caplog.text


# ARTICLES SANS COMPTES ============================================================================


def test_liste_articles_sans_comptes(
    logged_client, complet, make_edi_import, make_accounts_axe_pro_category
):
    """Première page : comptes recalculés puis lignes EDI sans compte listées"""
    article = complet["ok"]
    make_edi_import(
        "FOUR001",
        "OK-1",
        axe_pro=article.axe_pro,
        big_category=article.big_category,
        code_center="GAF",
        vat=None,
    )
    make_accounts_axe_pro_category(
        axe_pro=article.axe_pro, big_category=article.big_category, child_center="ACF", vat="001"
    )

    response = logged_client.get(reverse("articles:articles_without_account_list"))

    assert response.status_code == 200
    assert response.context["titre_table"] == "1.2 - Articles sans comptes"
    assert ArticleAccount.objects.filter(article=article, child_center="ACF", vat="001").exists()
    assert [row.reference for row in response.context["articles"]] == ["OK-1"]
    assert response.context["url_redirect"] == reverse("articles:articles_without_account_list")


def test_liste_articles_sans_comptes_pagination(logged_client):
    """Avec page : pas de recalcul, page hors bornes ramenée à la dernière"""
    response = logged_client.get(reverse("articles:articles_without_account_list"), {"page": "99"})

    assert response.status_code == 200
    assert response.context["articles"].number == 1
    assert response.context["num_items"] == 0


def test_export_articles_sans_comptes(logged_client, monkeypatch, caplog):
    """Export xlsx puis chemin d'erreur"""
    url = reverse("articles:articles_without_account_export_list")

    response = logged_client.get(url)
    assert response.status_code == 200
    assert "LISTING_DES_ARTICLES_SANS_COMPTES_" in response["Content-Disposition"]

    def _boom(*_args, **_kwargs):
        raise RuntimeError("xlsx")

    with (
        patched_attrs(monkeypatch, views_articles_with_no_account_etape_1_2, response_file=_boom),
        caplog.at_level(logging.ERROR, logger="export_excel"),
    ):
        response = logged_client.get(url)

    assert response.status_code == 302
    assert response.url == reverse("articles:articles_without_account_list")
    assert "view : articles_without_account_export_list" in caplog.text


def test_update_articles_without_account(logged_client, monkeypatch, caplog):
    """GET écran vide, POST lance l'import, exception journalisée"""
    from apps.articles.imports import articles_without_account  # pylint: disable=C0415

    url = reverse("articles:update_articles_without_account")

    response = logged_client.get(url)
    assert response.status_code == 200
    assert response.context["titre_table"] == "Import des articles sans comptes"

    with patched_attrs(
        monkeypatch,
        articles_without_account,
        import_articles_without_account=lambda: ("erreur", "ok"),
    ):
        response = logged_client.post(url)

    assert response.context["messages_errors"] == "erreur"
    assert response.context["messages_ok"] == "ok"

    def _boom():
        raise RuntimeError("répertoire")

    with (
        patched_attrs(monkeypatch, articles_without_account, import_articles_without_account=_boom),
        caplog.at_level(logging.ERROR, logger="export_excel"),
    ):
        response = logged_client.post(url)

    assert response.status_code == 200
    assert "view : update_articles_without_account" in caplog.text
