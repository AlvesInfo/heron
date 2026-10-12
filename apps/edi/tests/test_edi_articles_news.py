"""Tests de la codification des nouveaux articles importés (apps.edi.bin.edi_articles_news) :


amorçage Django du script, statistiques familles par regex, insertion des nouveaux articles,
report des axes sur les lignes importées.

created at: 2026-10-10
created by: Paulo ALVES
"""

import importlib
import platform
import sys
import types
from decimal import Decimal

import pytest
from django.db import connection

from apps.articles.models import Article
from apps.edi.bin import edi_articles_news
from apps.edi.tests.helpers_post import refresh
from conftest import patched_attrs

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    ("node", "expected"), [("MSI", r"C:\SitesWeb\heron"), ("serveur-prod", "/home/paulo/heron")]
)
def test_base_dir_selon_la_machine(monkeypatch, node, expected):
    monkeypatch.setattr(sys, "path", list(sys.path))

    try:
        with patched_attrs(monkeypatch, platform, uname=lambda: types.SimpleNamespace(node=node)):
            assert expected == importlib.reload(edi_articles_news).BASE_DIR
    finally:
        importlib.reload(edi_articles_news)


@pytest.fixture
def stat_acuitis(
    make_society,
    make_supplier_family_axes,
    make_section,
    make_big_category,
    make_sub_category,
    make_unit,
):
    """Tiers FOUR001 rattaché à la statistique ACUITIS : famille LUNETTES -> axe pro OPT"""
    big_category = make_big_category("Marchandises")
    family = make_supplier_family_axes(
        "LUNETTES",
        "ACUITIS",
        axe_pro=make_section("PRO", "OPT"),
        big_category=big_category,
        sub_category=make_sub_category("Solaires", big_category),
        customs_code="9004",
        item_weight=Decimal(3),
        unit_weight=make_unit(1, "U"),
    )
    make_society("FOUR001", is_client=False, stat_name=family.stat_name)
    return family


@pytest.mark.usefixtures("stat_acuitis")
def test_get_famillly_edi_ediimport_new_articles(edi_batch, make_article):
    make_article("ART-OLD")
    edi_batch(
        [{"reference_article": "ART-NEW", "famille": "LUNETTES"}, {"reference_article": "ART-OLD"}]
    )
    edi_batch([{"reference_article": "X"}], third_party_num="SANS001")

    with connection.cursor() as cursor:
        assert edi_articles_news.get_famillly_edi_ediimport_new_articles(cursor) == [
            ("FOUR001", "ACUITIS")
        ]


def test_set_axes_with_regex(
    edi_batch, stat_acuitis, make_default_axes, make_article, make_section, make_user
):
    defaults = make_default_axes()
    make_user(email="automate@acuitis.com", username="automate")
    refac = make_section("BU", "REFAC0")
    known = make_article(
        "ART-OLD", axe_pro=make_section("PRO", "AUD"), axe_bu=defaults.axe_bu, unit_weight=None
    )
    _, rows = edi_batch(
        [
            {
                "reference_article": "ART-NEW",
                "famille": "LUNETTES",
                "libelle": "Lunettes soleil",
                "net_unit_price": Decimal(15),
                "ean_code": "EAN1",
            },
            {"reference_article": "ART-OLD", "axe_pro": None},
            {"reference_article": "ART-UNK", "famille": "AUTRE"},
            {"reference_article": "RF-1", "famille": "LUNETTES", "third_party_num": "ZREFAC0"},
        ]
    )

    edi_articles_news.set_axes_with_regex()

    new, old, unknown, refac_row = refresh(*rows)
    # ligne codifiée par la statistique famille
    assert (new.axe_pro, new.big_category, new.sub_category) == (
        stat_acuitis.axe_pro,
        stat_acuitis.big_category,
        stat_acuitis.sub_category,
    )
    assert (new.axe_bu, new.customs_code, new.item_weight) == (
        defaults.axe_bu,
        "9004",
        Decimal(3),
    )
    # nouvel article créé depuis la ligne, flagué nouveau, sans erreur de sous-catégorie
    article = Article.objects.get(reference="ART-NEW", third_party_num="FOUR001")
    assert (article.new_article, article.libelle, article.catalog_price, article.ean_code) == (
        True,
        "Lunettes soleil",
        Decimal(15),
        "EAN1",
    )
    assert (article.axe_pro, article.axe_rfa, article.created_by.username) == (
        stat_acuitis.axe_pro,
        defaults.axe_rfa,
        "automate",
    )
    assert article.error_sub_category is False
    # article inconnu sans statistique : créé avec les axes par défaut et en erreur de sous-catégorie
    unknown_article = Article.objects.get(reference="ART-UNK")
    assert (unknown_article.axe_pro, unknown_article.big_category) == (None, defaults.big_category)
    assert unknown_article.error_sub_category is True
    assert unknown.big_category == defaults.big_category
    # article existant : les axes et l'unité par défaut sont reportés sur la ligne
    assert (old.axe_pro, old.axe_bu, old.unit_weight_id) == (known.axe_pro, defaults.axe_bu, 1)
    # tiers ZREFAC0 : BU forcée à REFAC0 (tiers sans statistique)
    assert refac_row.axe_bu == refac


def test_set_axes_with_regex_sans_nouveaux_articles(edi_batch, make_article):
    make_article("ART-1")
    edi_batch([{"reference_article": "ART-1"}])

    edi_articles_news.set_axes_with_regex()

    assert Article.objects.count() == 1
