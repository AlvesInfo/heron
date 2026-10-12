# pylint: disable=E0401,W0621,R0913
"""FR : Tests des vues des articles / comptes (views_article_accounts.py)


EN : Tests for articles accounts views

created at: 2026-10-10
created by: Paulo ALVES
"""

import logging

import pytest
from django.contrib.messages import get_messages
from django.urls import reverse

from apps.articles.models import ArticleAccount
from apps.articles.views import views_article_accounts
from apps.core.functions.functions_http_response import CONTENT_TYPE_EXCEL
from apps.core.models import ChangesTrace
from conftest import patched_attrs

pytestmark = pytest.mark.django_db


def _messages(response):
    return [str(message) for message in get_messages(response.wsgi_request)]


@pytest.fixture
def comptes(make_article, make_article_account, make_account, make_society):
    """Un article avec un compte ACF, un autre avec ACF + GAF, comptes du plan FRA"""
    for number in ("607000", "707000", "601000", "701000"):
        make_account("FRA", number)

    four = make_society("FOUR001", is_client=False)
    seul = make_article("SEUL", society=four)
    double = make_article("DOUBLE", society=four)
    return {
        "seul_acf": make_article_account(article=seul, child_center="ACF", vat="001"),
        "double_acf": make_article_account(article=double, child_center="ACF", vat="001"),
        "double_gaf": make_article_account(article=double, child_center="GAF", vat="001"),
    }


# LISTE ============================================================================================


@pytest.mark.usefixtures("comptes")
def test_liste_articles_comptes(logged_client):
    """Liste paginée avec filtres, titre avec le compte"""
    response = logged_client.get(reverse("articles:articles_account_list"))

    assert response.status_code == 200
    assert "(3 résultats)" in response.context["titre_table"]
    assert response.context["num_items"] == 3
    assert response.context["end_index"] == 3
    assert response.context["url_redirect"] == reverse("articles:articles_account_list")

    response = logged_client.get(reverse("articles:articles_account_list"), {"child_center": "GAF"})
    assert "(1 article / comptes)" in response.context["titre_table"]
    assert response.context["attrs_filter"] == {"child_center": "GAF"}

    assert (
        logged_client.get(reverse("articles:articles_account_list"), {"page": "99"})
        .context["articles"]
        .number
        == 1
    )
    assert (
        "résultats"
        not in logged_client.get(
            reverse("articles:articles_account_list"), {"reference": "ZZZ"}
        ).context["titre_table"]
    )


# UPDATE ===========================================================================================


def test_update_get(logged_client, comptes):
    """Titre et chevron vers la liste, filtres conservés dans l'url de retour"""
    account = comptes["seul_acf"]

    response = logged_client.get(
        reverse("articles:articles_account_update", args=(account.pk,)),
        {"child_center": "ACF", "page": "2"},
    )

    assert response.status_code == 200
    assert (
        response.context["titre_table"]
        == f"Modification des comptes de l'article {account.article}"
    )
    assert (
        response.context["chevron_retour"]
        == reverse("articles:articles_account_list") + "?child_center=ACF&page=2"
    )


def test_update_get_next_url(logged_client, comptes):
    """Le paramètre next est utilisé s'il est local, ignoré s'il est externe"""
    account = comptes["seul_acf"]
    url = reverse("articles:articles_account_update", args=(account.pk,))

    assert (
        logged_client.get(url, {"next": "/articles/fiche/"}).context["chevron_retour"]
        == "/articles/fiche/"
    )
    assert logged_client.get(url, {"next": "https://evil.example/x"}).context[
        "chevron_retour"
    ] == reverse("articles:articles_account_list")


def test_update_cree_le_miroir_gaf(logged_client, comptes):
    """Sans ligne GAF, elle est créée avec les mêmes comptes et tracée"""
    account = comptes["seul_acf"]

    response = logged_client.post(
        reverse("articles:articles_account_update", args=(account.pk,)) + "?next=/retour/",
        data={"purchase_account": "601000", "sale_account": "701000"},
    )

    account.refresh_from_db()
    mirror = ArticleAccount.objects.get(article=account.article, child_center="GAF", vat="001")
    assert response.status_code == 302
    assert response.url == "/retour/"
    assert (account.purchase_account, account.sale_account) == ("601000", "701000")
    assert (mirror.purchase_account, mirror.sale_account) == ("601000", "701000")
    assert _messages(response) == [
        f"Les comptes de l'article {account.article} - centrale ACF - tva 001 ont été modifiés avec success, compte GAF créé avec les mêmes comptes"
    ]
    assert ChangesTrace.objects.filter(model_name="articleaccount", action_type=1).count() == 1
    assert ChangesTrace.objects.filter(model_name="articleaccount", action_type=2).count() == 1


def test_update_aligne_le_miroir_gaf(logged_client, comptes):
    """La ligne GAF existante est alignée et tracée"""
    account = comptes["double_acf"]

    response = logged_client.post(
        reverse("articles:articles_account_update", args=(account.pk,)),
        data={"purchase_account": "601000", "sale_account": "707000"},
    )

    mirror = ArticleAccount.objects.get(pk=comptes["double_gaf"].pk)
    assert response.status_code == 302
    assert response.url == reverse("articles:articles_account_list")
    assert mirror.purchase_account == "601000"
    assert _messages(response)[0].endswith(", ainsi que pour la centrale GAF")
    assert ChangesTrace.objects.filter(model_name="articleaccount", action_type=2).count() == 2


def test_update_miroir_deja_identique(logged_client, comptes):
    """Si GAF a déjà les mêmes comptes, aucune trace supplémentaire"""
    account = comptes["double_acf"]
    ArticleAccount.objects.filter(pk=comptes["double_gaf"].pk).update(
        purchase_account="601000", sale_account="707000"
    )

    response = logged_client.post(
        reverse("articles:articles_account_update", args=(account.pk,)),
        data={"purchase_account": "601000", "sale_account": "707000"},
    )

    assert _messages(response)[0].endswith(", comptes GAF déjà identiques")
    assert ChangesTrace.objects.filter(model_name="articleaccount").count() == 1


def test_update_de_la_ligne_gaf_elle_meme(logged_client, comptes):
    """Modifier la ligne GAF ne cherche pas de miroir"""
    account = comptes["double_gaf"]

    response = logged_client.post(
        reverse("articles:articles_account_update", args=(account.pk,)),
        data={"purchase_account": "601000", "sale_account": "707000"},
    )

    acf = ArticleAccount.objects.get(pk=comptes["double_acf"].pk)
    assert response.status_code == 302
    assert acf.purchase_account == "607000"
    assert _messages(response)[0].endswith("tva 001 ont été modifiés avec success")


def test_update_invalide(logged_client, comptes):
    """Compte hors plan FRA refusé"""
    response = logged_client.post(
        reverse("articles:articles_account_update", args=(comptes["seul_acf"].pk,)),
        data={"purchase_account": "000000", "sale_account": "707000"},
    )

    assert response.status_code == 200
    assert "purchase_account" in response.context["form"].errors


# EXPORT PAR FOURNISSEUR ===========================================================================


@pytest.mark.usefixtures("comptes")
def test_export_par_fournisseur(logged_client, caplog):
    """GET affiche le formulaire, POST valide renvoie le xlsx, POST invalide journalise"""
    url = reverse("articles:articles_account_supplier_export")

    response = logged_client.get(url)
    assert response.status_code == 200
    assert response.context["titre_table"] == "12. Articles / Comptes par fournisseur"

    response = logged_client.post(url, data={"third_party_num": "FOUR001"})
    assert response.status_code == 200
    assert response["Content-Type"] == CONTENT_TYPE_EXCEL
    assert "LISTING_DES_ARTICLES_COMPTES_FOUR001_" in response["Content-Disposition"]

    with caplog.at_level(logging.ERROR, logger="export_excel"):
        response = logged_client.post(url, data={"third_party_num": "INCONNU"})

    assert response.status_code == 200
    assert response.context["form"].errors
    assert "erreur form" in caplog.text


@pytest.mark.usefixtures("comptes")
def test_export_par_fournisseur_en_erreur(logged_client, monkeypatch, caplog):
    """Exception à la génération : journalisée, écran réaffiché"""

    def _boom(*_args, **_kwargs):
        raise RuntimeError("xlsx")

    with (
        patched_attrs(monkeypatch, views_article_accounts, response_file=_boom),
        caplog.at_level(logging.ERROR, logger="export_excel"),
    ):
        response = logged_client.post(
            reverse("articles:articles_account_supplier_export"),
            data={"third_party_num": "FOUR001"},
        )

    assert response.status_code == 200
    assert "view : articles_account_supplier_export" in caplog.text


# UPDATE PAR FICHIER ===============================================================================


def test_update_articles_accounts_file(logged_client, monkeypatch, caplog):
    """GET écran vide, POST lance l'update, exception journalisée"""
    from apps.articles.imports import articles_update_account  # pylint: disable=C0415

    url = reverse("articles:update_articles_accounts_file")

    response = logged_client.get(url)
    assert response.status_code == 200
    assert response.context["titre_table"] == "13. Update des articles / comptes"

    with patched_attrs(
        monkeypatch, articles_update_account, update_articles_accounts=lambda: ("erreur", "ok")
    ):
        response = logged_client.post(url)

    assert response.context["messages_errors"] == "erreur"
    assert response.context["messages_ok"] == "ok"

    def _boom():
        raise RuntimeError("répertoire")

    with (
        patched_attrs(monkeypatch, articles_update_account, update_articles_accounts=_boom),
        caplog.at_level(logging.ERROR, logger="export_excel"),
    ):
        response = logged_client.post(url)

    assert response.status_code == 200
    assert "view : update_articles_accounts_file" in caplog.text
