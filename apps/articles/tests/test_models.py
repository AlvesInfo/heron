# pylint: disable=E0401,W0621,W0212
"""FR : Tests des modèles de l'app articles


EN : Tests for articles models

created at: 2026-10-10
created by: Paulo ALVES
"""

import datetime
from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from apps.articles.models import (
    Article,
    ArticleAccount,
    ArticleUpdate,
    SalePriceHistory,
    SellingPrice,
    Subscription,
    SubscriptionArticle,
)

pytestmark = pytest.mark.django_db


# ARTICLE ==========================================================================================


def test_article_creation_str_et_defauts(make_article):
    """Création, __str__ 'tiers - référence', défauts numériques et flags"""
    article = make_article("REF-1")

    assert str(article) == f"{article.third_party_num} - REF-1"
    assert article.item_weight == Decimal(0)
    assert article.packaging_qty == Decimal(1)
    assert article.unit_weight.num == 1
    assert article.customs_unit_weight.num == 1
    assert article.new_article is False
    assert article.error_sub_category is False
    assert article.axe_bu is None
    assert article.axe_rfa is None


def test_article_save_pose_les_axes_par_defaut(make_article, default_sections):
    """Sans axes, save() prend BU/CAHA, PRJ/NAF, PYS/FR et RFA/NAF s'ils existent"""
    article = make_article("REF-1")

    assert article.axe_bu == default_sections["BU"]
    assert article.axe_prj == default_sections["PRJ"]
    assert article.axe_pys == default_sections["PYS"]
    assert article.axe_rfa == default_sections["RFA"]
    assert article.axe_pro is None


def test_article_save_conserve_les_axes_fournis(make_article, default_sections, make_section):
    """Des axes explicites ne sont pas écrasés par les défauts"""
    bu = make_section("BU", "SUPPLY")
    rfa = make_section("RFA", "RFA01")

    article = make_article("REF-1", axe_bu=bu, axe_rfa=rfa)

    assert article.axe_bu == bu
    assert article.axe_rfa == rfa
    assert article.axe_pys == default_sections["PYS"]


def test_article_unicite_tiers_reference(make_article, make_society):
    """Le couple tiers/référence est unique, la même référence existe chez deux tiers"""
    make_article("REF-1", society=make_society("FOUR001", is_client=False))
    make_article("REF-1", society=make_society("FOUR002", is_client=False))
    society = make_society("FOUR001")

    with transaction.atomic(), pytest.raises(IntegrityError):
        make_article("REF-1", society=society)


def test_article_ordering(make_article, make_society):
    """Tri par tiers, création décroissante puis référence"""
    four2 = make_society("FOUR002", is_client=False)
    make_article("B", society=four2)
    make_article("A", society=make_society("FOUR001", is_client=False))

    assert list(Article.objects.values_list("reference", flat=True)) == ["A", "B"]


def test_article_tiers_protege(make_article):
    """Le tiers d'un article est protégé"""
    article = make_article()
    tiers = type(article.third_party_num).objects.filter(pk=article.third_party_num.pk)

    with pytest.raises(ProtectedError):
        tiers.delete()


# PRIX / ABONNEMENTS ===============================================================================


def test_selling_price_et_history(make_article, make_sale_price_category):
    """__str__, défauts devise et unicité des prix de vente et de leur historique"""
    article = make_article("REF-1")
    category = make_sale_price_category("Tarif A")
    price = SellingPrice.objects.create(
        sale_price_category=category, article=article, sale_price=Decimal("12.5")
    )
    history = SalePriceHistory.objects.create(
        sale_price_category=category,
        article=article,
        sale_price=Decimal("12.5"),
        start_date=Decimal(20260101),
        end_date=Decimal(20261231),
    )

    assert str(price) == f"{category} - {article}"
    assert price.currency == "EUR"
    assert str(history) == f"{category} - {article}"

    sale_price = Decimal(1)
    start_date = Decimal(20260101)
    end_date = Decimal(20261231)

    with transaction.atomic(), pytest.raises(IntegrityError):
        SellingPrice.objects.create(
            sale_price_category=category, article=article, sale_price=sale_price
        )

    with transaction.atomic(), pytest.raises(IntegrityError):
        SalePriceHistory.objects.create(
            sale_price_category=category,
            article=article,
            sale_price=sale_price,
            start_date=start_date,
            end_date=end_date,
        )


def test_subscription_et_subscription_article(make_article):
    """Abonnements et lignes d'abonnement : __str__, défaut qty, unicité, protection"""
    article = make_article("REF-1")
    price = SellingPrice.objects.create(article=article, sale_price=Decimal(9))
    subscription = Subscription.objects.create(name="Mensuel")
    line = SubscriptionArticle.objects.create(subscription=subscription, selling_price=price)

    assert str(subscription) == "Mensuel"
    assert str(line) == f"Mensuel - {price}"
    assert line.qty == Decimal(1)

    with transaction.atomic(), pytest.raises(IntegrityError):
        SubscriptionArticle.objects.create(subscription=subscription, selling_price=price)

    subscription_queryset = Subscription.objects.filter(pk=subscription.pk)

    with pytest.raises(ProtectedError):
        subscription_queryset.delete()


# COMPTES ==========================================================================================


def test_article_account_metadonnees_et_unicite(make_article_account):
    """Colonnes d'import, clés uniques, unicité centrale/article/tva, tri"""
    account = make_article_account(child_center="ACF", vat="001")
    make_article_account(article=account.article, child_center="ACF", vat="002")

    assert list(ArticleAccount.get_columns_import()) == [
        "article",
        "child_center",
        "vat",
        "purchase_account",
        "sale_account",
    ]
    assert list(ArticleAccount.get_columns_import().values()) == list(range(5))
    assert ArticleAccount.get_uniques() == {"child_center", "article", "vat"}
    assert list(ArticleAccount.objects.values_list("vat", flat=True)) == ["001", "002"]

    with transaction.atomic(), pytest.raises(IntegrityError):
        make_article_account(article=account.article, child_center="ACF", vat="001")


def test_article_account_protege_article_et_tva(make_article_account):
    """Article et tva référencés par un compte sont protégés"""
    account = make_article_account()
    article = Article.objects.filter(pk=account.article.pk)
    vat = type(account.vat).objects.filter(pk=account.vat.pk)

    with pytest.raises(ProtectedError):
        article.delete()

    with pytest.raises(ProtectedError):
        vat.delete()


def test_article_update(make_society):
    """Table d'import pour mise à jour des articles"""
    row = ArticleUpdate.objects.create(
        supplier=make_society("TECH001", is_client=False),
        reference="R1",
        libelle="L1",
        date_facture=datetime.date(2026, 1, 1),
    )

    assert row.supplier.third_party_num == "TECH001"
    assert row.ean_code is None
    assert ArticleUpdate.objects.count() == 1
