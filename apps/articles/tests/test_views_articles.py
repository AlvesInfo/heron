# pylint: disable=E0401,W0621,R0913
"""
FR : Tests des vues des articles (views_articles.py)
EN : Tests for articles views

created at: 2026-10-10
created by: Paulo ALVES
"""
import logging

import pytest
from django.contrib.messages import get_messages
from django.urls import reverse

from apps.articles.models import Article, ArticleAccount
from apps.articles.views import views_articles
from apps.core.functions.functions_http_response import CONTENT_TYPE_EXCEL
from apps.core.models import ChangesTrace
from conftest import patched_attrs

pytestmark = pytest.mark.django_db


def _messages(response):
    return [str(message) for message in get_messages(response.wsgi_request)]


@pytest.fixture
def catalogue(make_article, make_society, make_big_category, default_sections):
    """Deux fournisseurs, deux catégories"""
    four1 = make_society("FOUR001", is_client=False, name="Fournisseur un")
    four2 = make_society("FOUR002", is_client=False, name="Fournisseur deux")
    marchandises = make_big_category("Marchandises")
    verres = make_big_category("Verres")
    return {
        "four1": four1,
        "marchandises": marchandises,
        "a1": make_article("A-1", society=four1, big_category=marchandises, libelle="Monture A1", axe_pro=default_sections["PRO"]),
        "a2": make_article("A-2", society=four1, big_category=marchandises, libelle="Monture A2"),
        "v1": make_article("V-1", society=four1, big_category=verres, libelle="Verre V1"),
        "b1": make_article("B-1", society=four2, big_category=marchandises, libelle="Monture B1"),
    }


# LISTES ===========================================================================================


@pytest.mark.usefixtures('catalogue')
def test_fournisseurs_par_categorie(logged_client):
    """Fournisseurs ayant des articles dans la catégorie, avec le nombre d'articles"""
    response = logged_client.get(reverse("articles:suppliers_articles_list", args=("marchandises",)))

    assert response.status_code == 200
    assert response.context["titre_table"] == "Articles : Marchandises"
    assert list(response.context["suppliers"]) == [
        {"third_party_num": "FOUR001", "third_party_num__name": "Fournisseur un", "nb_articles": 2},
        {"third_party_num": "FOUR002", "third_party_num__name": "Fournisseur deux", "nb_articles": 1},
    ]


@pytest.mark.parametrize("ordering", ["-third_party_num", ("-third_party_num",)])
@pytest.mark.usefixtures('catalogue')
def test_fournisseurs_par_categorie_avec_ordering(logged_client, monkeypatch, ordering):
    """Un ordering de ListView (chaîne ou tuple) est appliqué au queryset agrégé"""
    with patched_attrs(monkeypatch, views_articles.SuppliersArticlesList, ordering=ordering):
        response = logged_client.get(reverse("articles:suppliers_articles_list", args=("marchandises",)))

    assert [row["third_party_num"] for row in response.context["suppliers"]] == ["FOUR002", "FOUR001"]


@pytest.mark.usefixtures('catalogue')
def test_articles_d_un_fournisseur(logged_client):
    """Articles du tiers dans la catégorie, chevron retour vers les fournisseurs"""
    response = logged_client.get(reverse("articles:articles_list", args=("FOUR001", "marchandises")))

    assert response.status_code == 200
    assert response.context["titre_table"] == "Articles : Marchandises du Tiers FOUR001"
    assert response.context["chevron_retour"] == reverse("articles:suppliers_articles_list", args=("marchandises",))
    assert {row["reference"] for row in response.context["articles"]} == {"A-1", "A-2"}
    assert response.context["articles"][0]["axe_pro__section"] in ("DIV", None)


# CREATE ===========================================================================================


@pytest.mark.usefixtures('catalogue')
def test_creation_get_pour_un_tiers(logged_client):
    """Création rattachée à un tiers : titre et chevron vers sa liste"""
    response = logged_client.get(reverse("articles:article_create", args=("FOUR001", "marchandises")))

    assert response.status_code == 200
    assert response.context["create"] is True
    assert response.context["base_create"] is False
    assert response.context["titre_table"] == "Création d'un Nouvel Article pour le Tiers : FOUR001"
    assert response.context["third_party_num"] == "FOUR001"
    assert response.context["chevron_retour"] == reverse("articles:articles_list", args=("FOUR001", "marchandises"))


@pytest.mark.usefixtures('catalogue')
def test_creation_get_generique(logged_client):
    """Création sans tiers ('create') : chevron vers les fournisseurs"""
    response = logged_client.get(reverse("articles:article_create", args=("create", "marchandises")))

    assert response.status_code == 200
    assert response.context["base_create"] is True
    assert response.context["chevron_retour"] == reverse("articles:suppliers_articles_list", args=("marchandises",))
    assert "third_party_num" not in response.context


def test_creation_post_valide(logged_client, article_post_data, make_edi_import, make_sub_category, make_big_category):
    """Création : créateur, trace, redirection vers la liste du tiers ; sous-catégorie incohérente effacée ; EDI mis à jour"""
    edi = make_edi_import("FOUR001", "REF-001")
    other_sub_category = make_sub_category("Autre rubrique", big_category=make_big_category("Verres"))

    response = logged_client.post(
        reverse("articles:article_create", args=("FOUR001", "marchandises")),
        data={**article_post_data, "sub_category": str(other_sub_category.uuid_identification)},
    )

    article = Article.objects.get(reference="REF-001")
    edi.refresh_from_db()
    assert response.status_code == 302
    assert response.url == reverse("articles:articles_list", args=("FOUR001", "marchandises"))
    assert article.created_by == logged_client.user
    assert article.sub_category is None
    assert article.axe_bu.section == "CAHA"
    assert edi.axe_pro == article.axe_pro
    assert edi.big_category == article.big_category
    assert edi.axe_bu == article.axe_bu
    assert ChangesTrace.objects.filter(model_name="article", action_type=1).count() == 1
    assert "L'Article REF-001 a été créé avec success" in _messages(response)


def test_creation_post_generique_sous_categorie_coherente(logged_client, article_post_data, make_sub_category, make_big_category):
    """Route 'create' : la sous-catégorie de la bonne catégorie est conservée"""
    sub_category = make_sub_category("Montures", big_category=make_big_category("Marchandises"))

    response = logged_client.post(
        reverse("articles:article_create", args=("create", "marchandises")),
        data={**article_post_data, "sub_category": str(sub_category.uuid_identification)},
    )

    assert response.status_code == 302
    assert Article.objects.get(reference="REF-001").sub_category == sub_category


def test_creation_post_invalide(logged_client, article_post_data, caplog):
    """Référence manquante : formulaire réaffiché"""
    with caplog.at_level(logging.ERROR, logger="error_views"):
        response = logged_client.post(reverse("articles:article_create", args=("FOUR001", "marchandises")), data={**article_post_data, "reference": ""})

    assert response.status_code == 200
    assert response.context["form"].errors["reference"]
    assert "ChangeTraceMixin error" in caplog.text


# UPDATE ===========================================================================================


def test_modification_get(logged_client, catalogue, make_article_account):
    """Contexte : titre, chevron, comptes de la centrale ACF uniquement"""
    article = catalogue["a1"]
    acf = make_article_account(article=article, child_center="ACF", vat="001")
    make_article_account(article=article, child_center="GAF", vat="001")

    response = logged_client.get(reverse("articles:article_update", args=("FOUR001", article.pk)))

    assert response.status_code == 200
    assert response.context["titre_table"] == f"Mise à jour Article {article}"
    assert response.context["article"] == "Article Référence : A-1"
    assert response.context["chevron_retour"] == reverse("articles:articles_list", args=("FOUR001", "marchandises"))
    assert list(response.context["accounts"]) == [acf]


def test_modification_post(logged_client, catalogue, article_post_data, make_edi_import):
    """Modification : modificateur, trace, EDI mis à jour, redirection"""
    article = catalogue["a1"]
    edi = make_edi_import("FOUR001", "A-1")

    response = logged_client.post(
        reverse("articles:article_update", args=("FOUR001", article.pk)),
        data={**article_post_data, "reference": "A-1", "libelle": "Monture modifiée"},
    )

    article.refresh_from_db()
    edi.refresh_from_db()
    assert response.status_code == 302
    assert response.url == reverse("articles:articles_list", args=("FOUR001", "marchandises"))
    assert article.libelle == "Monture modifiée"
    assert article.modified_by == logged_client.user
    assert edi.axe_pro == article.axe_pro
    assert "L'Article A-1 a été modifié avec success" in _messages(response)


def test_modification_post_sous_categorie_incoherente(logged_client, catalogue, article_post_data, make_sub_category, make_big_category):
    """Une rubrique d'une autre catégorie est effacée à la modification"""
    article = catalogue["a1"]
    other = make_sub_category("Autre", big_category=make_big_category("Verres"))

    logged_client.post(
        reverse("articles:article_update", args=("FOUR001", article.pk)),
        data={**article_post_data, "reference": "A-1", "sub_category": str(other.uuid_identification)},
    )

    article.refresh_from_db()
    assert article.sub_category is None


# RECHERCHE ========================================================================================


@pytest.mark.usefixtures('catalogue')
def test_recherche_articles(logged_client):
    """Sans filtre : tous les articles, titre avec le compte"""
    response = logged_client.get(reverse("articles:articles_search_list"))

    assert response.status_code == 200
    assert "(4 articles trouvés)" in response.context["titre_table"]
    assert response.context["num_items"] == 4
    assert response.context["num_pages"] == 1
    assert response.context["start_index"] == 0
    assert response.context["end_index"] == 4


@pytest.mark.usefixtures('catalogue')
def test_recherche_articles_filtres_et_pagination(logged_client):
    """Filtres icontains, un seul résultat, page hors bornes et page non numérique"""
    url = reverse("articles:articles_search_list")

    response = logged_client.get(url, {"reference__icontains": "V-1"})
    assert "(1 article trouvé)" in response.context["titre_table"]
    assert response.context["attrs_filter"] == {"reference__icontains": "V-1"}
    assert response.context["form"].initial == {}
    assert response.context["form"].data["reference__icontains"] == "V-1"

    response = logged_client.get(url, {"reference__icontains": "ZZZ"})
    assert "trouvé" not in response.context["titre_table"]
    assert response.context["num_items"] == 0

    assert logged_client.get(url, {"page": "99"}).context["articles"].number == 1
    assert logged_client.get(url, {"page": "abc"}).context["articles"].number == 1


# EXPORT ===========================================================================================


@pytest.mark.usefixtures('catalogue')
def test_export_articles(logged_client):
    """Export xlsx des articles d'un fournisseur / catégorie"""
    response = logged_client.get(reverse("articles:articles_export_list", args=("FOUR001", "marchandises")))

    assert response.status_code == 200
    assert response["Content-Type"] == CONTENT_TYPE_EXCEL
    assert "LISTING_DES_ARTICLES_" in response["Content-Disposition"]


@pytest.mark.usefixtures('catalogue')
def test_export_articles_en_erreur(logged_client, monkeypatch, caplog):
    """Erreur : journalisée et redirection vers la liste du tiers"""

    def _boom(*_args, **_kwargs):
        raise RuntimeError("xlsx")

    with patched_attrs(monkeypatch, views_articles, response_file=_boom), caplog.at_level(logging.ERROR, logger="export_excel"):
        response = logged_client.get(reverse("articles:articles_export_list", args=("FOUR001", "marchandises")))

    assert response.status_code == 302
    assert response.url == reverse("articles:articles_list", args=("FOUR001", "marchandises"))
    assert "view : articles_export_list" in caplog.text


# COMPTES PAR TVA ==================================================================================


def test_compte_tva_create(logged_client, catalogue, make_child_center, make_vat):
    """GET (numéro du prochain compte) puis création et retour sur la fiche article"""
    article = catalogue["a1"]
    make_child_center("ACF")
    make_vat("001")
    url = reverse("articles:articles_account_vat_create", args=(article.pk,))

    response = logged_client.get(url)
    assert response.status_code == 200
    assert response.context["article"] == article
    assert response.context["article_new"] == 1
    assert response.context["titre_table"] == f"Article : {article}"
    assert response.context["chevron_retour"] == reverse("articles:article_update", kwargs={"third_party_num": "FOUR001", "pk": article.pk})

    response = logged_client.post(url, data={"child_center": "ACF", "article": str(article.uuid_identification), "vat": "001", "purchase_account": "607000", "sale_account": "707000"})

    account = ArticleAccount.objects.get()
    assert response.status_code == 302
    assert response.url == reverse("articles:article_update", kwargs={"third_party_num": "FOUR001", "pk": article.pk})
    assert account.article == article
    assert (account.purchase_account, account.sale_account) == ("607000", "707000")
    assert "a été créé avec success" in _messages(response)[0]


def test_compte_tva_create_article_inconnu(logged_client):
    """Article inexistant : 404 en GET comme en POST"""
    url = reverse("articles:articles_account_vat_create", args=(999999,))

    assert logged_client.get(url).status_code == 404
    assert logged_client.post(url, data={}).status_code == 404


def test_compte_tva_create_invalide(logged_client, catalogue):
    """Données vides : formulaire réaffiché"""
    response = logged_client.post(reverse("articles:articles_account_vat_create", args=(catalogue["a1"].pk,)), data={})

    assert response.status_code == 200
    assert response.context["form"].errors


def test_compte_tva_delete(ajax_client, logged_client, make_article_account, caplog):
    """Suppression ajax, pk inconnu, mauvaises requêtes"""
    account = make_article_account()
    url = reverse("articles:delete_articles_account_vat")

    assert ajax_client.get(url).url == reverse("home")
    assert logged_client.post(url, data={"pk": account.pk}).url == reverse("home")

    assert ajax_client.post(url, data={"pk": account.pk}).json() == {"success": "success"}
    assert not ArticleAccount.objects.exists()

    with caplog.at_level(logging.ERROR, logger="error_views"):
        assert ajax_client.post(url, data={"pk": account.pk}).json() == {"success": "ko"}

    assert "delete_articles_account_vat, form invalid" in caplog.text
