# pylint: disable=E0401,W0621
"""FR : Tests des formulaires, du schéma djantic, des filtres et des querysets de l'app articles


EN : Tests for articles forms, djantic schema, filters and querysets

created at: 2026-10-10
created by: Paulo ALVES
"""

import datetime
import uuid

import pytest
from pydantic import ValidationError

from apps.articles import forms as articles_forms
from apps.articles.filters import ArticleAccountFilter, ArticleFilter
from apps.articles.forms import (
    ArticleAccountForm,
    ArticleAccountSageSchema,
    ArticleAccountSupplierForm,
    ArticleAccountUpdateForm,
    ArticleForm,
    ArticleSearchForm,
    DeleteArticleAccountForm,
)
from apps.articles.models import Article, ArticleAccount
from apps.articles.parameters import querysets

pytestmark = pytest.mark.django_db


# FORMS ============================================================================================


@pytest.mark.usefixtures("make_sub_category")
def test_article_form_valide(article_post_data):
    """Création d'un article par le formulaire, sous-catégorie facultative"""
    form = ArticleForm(data=article_post_data)

    assert not form.fields["sub_category"].required
    assert form.is_valid(), form.errors
    article = form.save()
    assert article.reference == "REF-001"
    assert article.axe_bu.section == "CAHA"


def test_article_form_invalide():
    """Sans tiers ni référence : erreurs"""
    form = ArticleForm(data={})

    assert not form.is_valid()
    assert {"third_party_num", "reference"} <= set(form.errors)


def test_article_search_form_champs_ajoutes(make_article):
    """Les champs de recherche icontains sont ajoutés, aucun n'est requis, libellés corrects"""
    make_article()
    form = ArticleSearchForm({})

    assert form.is_valid()
    assert {"reference__icontains", "libelle__icontains", "libelle_heron__icontains"} <= set(
        form.fields
    )
    assert form.fields["libelle__icontains"].label == "Libellé"
    assert form.fields["libelle_heron__icontains"].label == "Libellé Héron"
    assert not any(field.required for field in form.fields.values())


def test_article_account_form(make_article, make_child_center, make_vat):
    """Création d'un compte article par le formulaire"""
    article = make_article()
    make_child_center("ACF")
    make_vat("001")

    form = ArticleAccountForm(
        data={
            "child_center": "ACF",
            "article": str(article.uuid_identification),
            "vat": "001",
            "purchase_account": "607000",
            "sale_account": "707000",
        }
    )

    assert form.is_valid(), form.errors
    assert form.save().article == article
    assert not ArticleAccountForm(data={}).is_valid()


def test_article_account_update_form_choix(make_article_account, make_account):
    """Les comptes proposés sont ceux du plan FRA, le compte actuel hors plan reste sélectionnable"""
    make_account("FRA", "607000", name="Achats")
    make_account("FRA", "707000", name="Ventes")
    make_account("BEL", "999999")
    account = make_article_account(purchase_account="606000", sale_account="707000")

    form = ArticleAccountUpdateForm(instance=account)

    assert form.fields["purchase_account"].choices == [
        ("", "---------"),
        ("606000", "606000 - (hors plan FRA)"),
        ("607000", "607000 - Achats"),
        ("707000", "707000 - Ventes"),
    ]
    assert form.fields["sale_account"].choices == [
        ("", "---------"),
        ("607000", "607000 - Achats"),
        ("707000", "707000 - Ventes"),
    ]

    form = ArticleAccountUpdateForm(
        instance=account, data={"purchase_account": "607000", "sale_account": "707000"}
    )
    assert form.is_valid(), form.errors
    assert form.save().purchase_account == "607000"

    form = ArticleAccountUpdateForm(
        instance=account, data={"purchase_account": "999999", "sale_account": "707000"}
    )
    assert not form.is_valid()
    assert set(form.errors) == {"purchase_account"}


def test_delete_article_account_form(make_article_account):
    """Valide avec un id existant, invalide sinon"""
    account = make_article_account()

    form = DeleteArticleAccountForm({"id": account.pk})
    assert form.is_valid()
    assert form.cleaned_data["id"] == account
    assert not DeleteArticleAccountForm({"id": account.pk + 100}).is_valid()
    assert not DeleteArticleAccountForm({"id": None}).is_valid()


def test_article_account_supplier_form(make_article_account, make_society):
    """Seuls les fournisseurs ayant des articles avec comptes sont proposés"""
    account = make_article_account()
    make_society("SANS001", is_client=False)

    form = ArticleAccountSupplierForm()

    assert list(form.fields["third_party_num"].queryset) == [account.article.third_party_num]
    assert ArticleAccountSupplierForm(
        {"third_party_num": account.article.third_party_num.third_party_num}
    ).is_valid()
    assert not ArticleAccountSupplierForm({"third_party_num": "SANS001"}).is_valid()


def test_package_forms():
    """Le package forms ré-exporte formulaires Django et schéma djantic"""
    assert articles_forms.ArticleForm is ArticleForm
    assert articles_forms.ArticleAccountSageSchema is ArticleAccountSageSchema


# DJANTIC ==========================================================================================


def test_article_account_schema():
    """Config, conversion des types, article obligatoire"""
    article_uuid = "6fa459ea-ee8a-3ca4-894e-db77e160355e"

    assert ArticleAccountSageSchema.model_config["model"] is ArticleAccount
    assert ArticleAccountSageSchema.model_config["include"] == [
        *list(ArticleAccount.get_columns_import()),
        "created_at",
        "modified_at",
    ]

    validated = ArticleAccountSageSchema(
        article=article_uuid,
        child_center="ACF",
        vat="001",
        purchase_account="607000",
        sale_account="707000",
    ).dict()
    assert validated["article"] == uuid.UUID(article_uuid)
    assert validated["child_center"] == "ACF"
    assert validated["vat"] == "001"
    assert isinstance(validated["created_at"], datetime.datetime)

    with pytest.raises(ValidationError) as excinfo:
        ArticleAccountSageSchema(
            child_center="ACF", vat="001", purchase_account="607000", sale_account="707000"
        )

    assert {error["loc"][0] for error in excinfo.value.errors()} == {"article"}


# FILTRES ==========================================================================================


def test_article_filter(make_article, make_society, make_big_category):
    """Filtre des articles : tiers exact, référence/libellé icontains, catégorie"""
    four1 = make_society("FOUR001", is_client=False)
    marchandises = make_big_category("Marchandises")
    monture = make_article(
        "MONT-1", society=four1, libelle="Monture dorée", big_category=marchandises
    )
    make_article(
        "VERRE-1", society=four1, libelle="Verre", big_category=make_big_category("Verres")
    )
    make_article("MONT-2", society=make_society("FOUR002", is_client=False), libelle="Monture")

    assert set(
        ArticleFilter({"reference__icontains": "mont"}, queryset=Article.objects.all()).qs
    ) == {monture, Article.objects.get(reference="MONT-2")}
    assert list(
        ArticleFilter(
            {"third_party_num": "FOUR001", "libelle__icontains": "dor"},
            queryset=Article.objects.all(),
        ).qs
    ) == [monture]
    assert list(
        ArticleFilter(
            {"big_category": str(marchandises.uuid_identification)}, queryset=Article.objects.all()
        ).qs
    ) == [monture]
    assert ArticleFilter({}, queryset=Article.objects.all()).qs.count() == 3


def test_article_account_filter(
    make_article_account, make_article, make_society, make_section, make_big_category
):
    """Filtre des articles / comptes sur la vue annotée"""
    pro = make_section("PRO", "OPT")
    four1 = make_society("FOUR001", is_client=False)
    article = make_article(
        "MONT-1",
        society=four1,
        libelle="Monture",
        libelle_heron="",
        axe_pro=pro,
        big_category=make_big_category("Marchandises"),
    )
    account = make_article_account(
        article=article,
        child_center="ACF",
        vat="001",
        purchase_account="607000",
        sale_account="707000",
    )
    other = make_article_account(
        article=make_article(
            "AUTRE", society=make_society("FOUR002", is_client=False), libelle_heron="Héron"
        ),
        child_center="GAF",
        vat="002",
        purchase_account="601000",
        sale_account="701000",
    )
    queryset = querysets.articles_with_account_queryset

    def _pks(data):
        return [row["pk"] for row in ArticleAccountFilter(data, queryset=queryset).qs]

    assert _pks({}) == [account.pk, other.pk]
    assert _pks({"child_center": "ACF"}) == [account.pk]
    assert _pks({"third_party_num": "FOUR001"}) == [account.pk]
    assert _pks({"reference": "mont"}) == [account.pk]
    assert _pks({"libelle": "héron"}) == [other.pk]
    assert _pks({"axe_pro": str(pro.uuid_identification)}) == [account.pk]
    assert _pks({"big_category": str(article.big_category.uuid_identification)}) == [account.pk]
    assert _pks({"vat": "002"}) == [other.pk]
    assert _pks({"purchase_account": "6070"}) == [account.pk]
    assert _pks({"sale_account": "7010"}) == [other.pk]
    assert list(
        ArticleAccountFilter({}, queryset=queryset).form.fields["third_party_num"].queryset
    ) == [four1, other.article.third_party_num]


# QUERYSETS ========================================================================================


def test_articles_with_account_queryset(make_article_account, make_article, make_sub_category):
    """Annotations libellé (héron prioritaire) et rubrique (vide si absente)"""
    sub_category = make_sub_category("Montures")
    with_heron = make_article_account(
        article=make_article("A", libelle="Brut", libelle_heron="Héron", sub_category=sub_category)
    )
    without = make_article_account(
        article=make_article("B", libelle="Brut seul", libelle_heron=None)
    )

    rows = {row["pk"]: row for row in querysets.articles_with_account_queryset}

    assert rows[with_heron.pk]["libelle_article"] == "Héron"
    assert rows[with_heron.pk]["sub_categoryc"] == "Montures"
    assert rows[without.pk]["libelle_article"] == "Brut seul"
    assert rows[without.pk]["sub_categoryc"] == ""


def test_articles_without_account_queryset_vide():
    """La requête brute des articles sans comptes s'exécute sur une base vide"""
    assert list(querysets.articles_without_account_queryset) == []


def test_articles_accounts_est_une_sous_requete():
    """articles_accounts est destiné à OuterRef : non évaluable seul"""
    with pytest.raises(ValueError, match="outer query"):
        list(querysets.articles_accounts)
