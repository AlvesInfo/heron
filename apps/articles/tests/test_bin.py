# pylint: disable=E0401,W0621
"""
FR : Tests des modules bin de l'app articles (sous-catégorie, requêtes, transferts BBGR, imports B.I)
EN : Tests for articles bin modules

created at: 2026-10-10
created by: Paulo ALVES
"""
import logging
import uuid
from decimal import Decimal

import pytest

from apps.articles.bin import (
    bbgr_002_articles,
    bbgr_003_articles,
    bbgr_004_articles,
    bbgr_006_articles,
    transfert_receptions,
)
from apps.articles.bin.articles_queries import get_article, get_articles
from apps.articles.bin.sub_category import check_sub_category
from apps.articles.loops import imports_articles
from apps.articles.models import Article, ArticleAccount
from conftest import patched_attrs

pytestmark = pytest.mark.django_db


# SOUS-CATÉGORIE ===================================================================================


def test_check_sub_category(make_sub_category, make_big_category):
    """Vraie si la rubrique appartient à la catégorie, fausse sinon"""
    category = make_big_category("Marchandises")
    sub_category = make_sub_category("Montures", big_category=category)

    assert check_sub_category(sub_category.uuid_identification, category.uuid_identification) is True
    assert check_sub_category(sub_category.uuid_identification, make_big_category("Verres").uuid_identification) is False
    assert check_sub_category(uuid.uuid4(), category.uuid_identification) is False


# REQUÊTES =========================================================================================


def test_get_articles_et_get_article(make_article, make_sub_category):
    """Dictionnaires des articles : libellé héron prioritaire, clés renommées"""
    heron = make_article("A", libelle="Brut", libelle_heron="Héron", customs_code="9003", sub_category=make_sub_category("Montures"))
    brut = make_article("B", libelle="Brut seul", libelle_heron="")

    articles = get_articles([heron.pk, brut.pk, 999999])

    assert set(articles) == {heron.pk, brut.pk}
    assert articles[heron.pk]["libelle"] == "Héron"
    assert articles[heron.pk]["reference_article"] == "A"
    assert articles[brut.pk]["libelle"] == "Brut seul"
    assert set(articles[heron.pk]) == {"reference_article", "ean_code", "libelle", "famille", "axe_bu", "axe_prj", "axe_pro", "axe_pys", "axe_rfa", "big_category", "sub_category", "customs_code", "item_weight"}

    article = get_article(heron.pk)
    assert article["libelle"] == "Héron"
    assert article["unit_weight"] == 1
    assert article["customs_code"] == "9003"
    assert get_article(999999) is None


# TRANSFERT DES RÉCEPTIONS BBGR001 -> BBGR006 ======================================================


@pytest.fixture
def receptions(make_society, make_article, make_article_account):
    """Articles de réception chez BBGR001 avec un compte, et le tiers BBGR006"""
    bbgr001 = make_society("BBGR001", is_client=False)
    make_society("BBGR006", is_client=False)
    plv = make_article("PLV-PLV", society=bbgr001, libelle="PLV")
    make_article("FRAMES-MONTURE OPT", society=bbgr001, libelle="Montures")
    make_article("HORS-LISTE", society=bbgr001)
    make_article_account(article=plv, child_center="ACF", vat="001", purchase_account="607000", sale_account="707000")
    return bbgr001


@pytest.mark.usefixtures('receptions')
def test_transfert_receptions_articles(caplog):
    """Les articles listés sont copiés chez BBGR006, pas les autres ; second passage sans doublon"""
    caplog.set_level(logging.INFO, logger="imports")
    transfert_receptions.transfert_receptions_articles()

    copies = set(Article.objects.filter(third_party_num="BBGR006").values_list("reference", flat=True))
    assert copies == {"PLV-PLV", "FRAMES-MONTURE OPT"}
    assert "True" in caplog.text

    transfert_receptions.transfert_receptions_articles()

    assert Article.objects.filter(third_party_num="BBGR006").count() == 2
    assert "False" in caplog.text


@pytest.mark.usefixtures('receptions')
def test_transfert_receptions_articles_conflit(make_article, make_society, caplog):
    """Une copie existante avec d'autres valeurs provoque une IntegrityError avalée"""
    caplog.set_level(logging.INFO, logger="imports")
    make_article("PLV-PLV", society=make_society("BBGR006"), libelle="Autre libellé")

    transfert_receptions.transfert_receptions_articles()

    assert "duplicate key" in caplog.text


@pytest.mark.usefixtures('receptions')
def test_transfert_receptions_articles_article_introuvable(monkeypatch, caplog):
    """La branche DoesNotExist (défensive) est journalisée"""
    caplog.set_level(logging.INFO, logger="imports")

    class _Manager:
        @staticmethod
        def filter(*args, **kwargs):
            return Article.objects.filter(*args, **kwargs)

        @staticmethod
        def get_or_create(**_kwargs):
            raise Article.DoesNotExist("article introuvable")

    class _FakeArticle:
        objects = _Manager()
        DoesNotExist = Article.DoesNotExist

    with patched_attrs(monkeypatch, transfert_receptions, Article=_FakeArticle):
        transfert_receptions.transfert_receptions_articles()

    assert sum("article introuvable" in record.getMessage() for record in caplog.records) == 2


@pytest.mark.usefixtures('receptions')
def test_transfert_receptions_accounts(caplog):
    """Les comptes des articles copiés sont recréés chez BBGR006 ; sans copie, DoesNotExist affiché"""
    caplog.set_level(logging.INFO, logger="imports")
    transfert_receptions.transfert_receptions_accounts()
    assert "Article matching query does not exist" in caplog.text

    transfert_receptions.transfert_receptions_articles()
    transfert_receptions.transfert_receptions_accounts()

    copy = ArticleAccount.objects.get(article__third_party_num="BBGR006")
    assert (copy.purchase_account, copy.sale_account, copy.vat.vat, copy.child_center.code) == ("607000", "707000", "001", "ACF")

    ArticleAccount.objects.filter(pk=copy.pk).update(purchase_account="999999")
    transfert_receptions.transfert_receptions_accounts()
    assert "duplicate key" in caplog.text


# INTÉGRATION B.I DES ARTICLES BBGR ================================================================


def _articles(third_party_num):
    return {a.reference: a for a in Article.objects.filter(third_party_num=third_party_num)}


def test_insert_bbgr_002_articles(bi_articles_table, make_default_axes, make_supplier_family_axes, make_country):
    """BBGR002 : prix de revient aval, axes par défaut, axe pro par famille, pays traduit, SAV exclu"""
    axes = make_default_axes()
    family = make_supplier_family_axes("LUNETTES")
    make_country("FR")
    make_country("CN")
    bi_articles_table(code_ean="EAN1", famille="LUNETTES", made_in="France", code_rayon="OPT")
    bi_articles_table(code_ean="EAN2", famille="AUTRE", made_in="RPC", code_rayon="OPT", poids=None)
    bi_articles_table(code_ean="EAN3", famille="SAV", code_rayon="OPT")
    bi_articles_table(code_ean="EAN4", famille="LUNETTES", code_rayon="SAV")
    bi_articles_table(code_ean="EAN5", made_in="Atlantide")

    bbgr_002_articles.insert_bbgr_002_articles()

    articles = _articles("BBGR002")
    assert set(articles) == {"EAN1", "EAN2", "EAN5"}
    assert articles["EAN1"].catalog_price == Decimal("10")
    assert articles["EAN1"].axe_pro == family.axe_pro
    assert articles["EAN1"].made_in.country == "FR"
    assert articles["EAN1"].axe_bu == axes.axe_bu
    assert articles["EAN1"].big_category == axes.big_category
    assert articles["EAN1"].new_article is True
    assert articles["EAN2"].made_in.country == "CN"
    assert articles["EAN2"].axe_pro is None
    assert articles["EAN2"].item_weight == 0
    assert articles["EAN5"].made_in is None

    bbgr_002_articles.insert_bbgr_002_articles()
    assert Article.objects.filter(third_party_num="BBGR002").count() == 3


def test_insert_bbgr_003_articles(bi_articles_table, make_default_axes, make_supplier_family_axes):
    """BBGR003 : prix de cession"""
    make_default_axes()
    make_supplier_family_axes("LUNETTES")
    bi_articles_table(code_ean="EAN1")

    bbgr_003_articles.insert_bbgr_003_articles()

    assert _articles("BBGR003")["EAN1"].catalog_price == Decimal("20")


def test_insert_bbgr_004_articles(bi_articles_table, make_default_axes, make_supplier_family_axes):
    """BBGR004 : une référence préfixée par type de retour (D1-, D2-, D3-, F-)"""
    make_default_axes()
    make_supplier_family_axes("LUNETTES")
    bi_articles_table(code_ean="EAN1")

    bbgr_004_articles.insert_bbgr_004_articles()

    assert set(_articles("BBGR004")) == {"D1-EAN1", "D2-EAN1", "D3-EAN1", "F-EAN1"}
    assert all(a.ean_code == "EAN1" and a.catalog_price == Decimal("20") for a in _articles("BBGR004").values())


def test_insert_bbgr_006_articles(bi_articles_table, make_default_axes, make_supplier_family_axes, make_section):
    """BBGR006 : rayons MO/MS sur l'axe BU SUPPLY, les autres sur l'axe BU par défaut"""
    axes = make_default_axes()
    make_supplier_family_axes("LUNETTES")
    supply = make_section("BU", "SUPPLY")
    bi_articles_table(code_ean="EAN-MO", code_rayon="MO")
    bi_articles_table(code_ean="EAN-OPT", code_rayon="OPT")

    bbgr_006_articles.insert_bbgr_006_articles()

    articles = _articles("BBGR006")
    assert articles["EAN-MO"].axe_bu == supply
    assert articles["EAN-OPT"].axe_bu == axes.axe_bu


def test_insert_bbgr_sans_parametrage_des_axes(bi_articles_table):
    """Sans ligne d'axes par défaut, le produit cartésien est vide : rien n'est inséré"""
    bi_articles_table(code_ean="EAN1")

    bbgr_002_articles.insert_bbgr_002_articles()

    assert not Article.objects.filter(third_party_num="BBGR002").exists()


# BOUCLE SUPERVISOR ================================================================================


def test_imports_articles_main(monkeypatch, caplog):
    """main() enchaîne les quatre imports et journalise les erreurs sans s'arrêter"""
    calls = []

    def _ok(name):
        return lambda: calls.append(name)

    def _boom():
        raise RuntimeError("B.I indisponible")

    with patched_attrs(
        monkeypatch, imports_articles,
        insert_bbgr_002_articles=_ok("002"), insert_bbgr_003_articles=_boom,
        insert_bbgr_004_articles=_ok("004"), insert_bbgr_006_articles=_boom,
    ), caplog.at_level(logging.ERROR, logger="edi"):
        imports_articles.main()

    assert calls == ["002", "004"]
    assert caplog.text.count("Exception Générale") == 2
    assert "insert_bbgr_003_articles()" in caplog.text
    assert "insert_bbgr_006_articles()" in caplog.text


def test_imports_articles_main_tout_en_erreur(monkeypatch, caplog):
    """Chaque import en erreur est journalisé indépendamment"""

    def _boom():
        raise RuntimeError("B.I indisponible")

    with patched_attrs(
        monkeypatch, imports_articles,
        insert_bbgr_002_articles=_boom, insert_bbgr_003_articles=_boom, insert_bbgr_004_articles=_boom, insert_bbgr_006_articles=_boom,
    ), caplog.at_level(logging.ERROR, logger="edi"):
        imports_articles.main()

    assert caplog.text.count("Exception Générale") == 4
    assert "insert_bbgr_002_articles()" in caplog.text
    assert "insert_bbgr_004_articles()" in caplog.text
