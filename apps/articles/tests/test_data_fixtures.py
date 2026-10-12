# pylint: disable=E0401,W0621
"""FR : Tests des scripts de fixtures des articles (data_fixtures/articles_fixtures.py)


EN : Tests for articles fixtures scripts

created at: 2026-10-10
created by: Paulo ALVES
"""

import logging
from decimal import Decimal

import pytest

from apps.articles.data_fixtures import articles_fixtures
from apps.articles.models import Article, ArticleUpdate
from conftest import patched_attrs

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _clear_caches():
    articles_fixtures.get_axe_pro.cache_clear()
    articles_fixtures.get_society.cache_clear()
    yield
    articles_fixtures.get_axe_pro.cache_clear()
    articles_fixtures.get_society.cache_clear()


def test_get_axe_pro_et_get_society(make_section, make_society):
    """Accès mis en cache aux sections PRO et aux tiers"""
    section = make_section("PRO", "OPT")
    society = make_society("FOUR001")

    assert articles_fixtures.get_axe_pro("OPT") == section
    assert articles_fixtures.get_society("FOUR001") == society
    assert articles_fixtures.get_axe_pro.cache_info().hits == 0
    articles_fixtures.get_axe_pro("OPT")
    assert articles_fixtures.get_axe_pro.cache_info().hits == 1


def test_import_articles(tmp_path, monkeypatch, make_section, make_society, make_unit, caplog):
    """Import du fichier texte : libellés par défaut = référence, update_or_create"""
    caplog.set_level(logging.INFO, logger="imports")
    make_section("PRO", "OPT")
    make_society("FOUR001", is_client=False)
    make_unit(1, "U")
    data_dir = tmp_path / "apps" / "articles" / "data_fixtures"
    data_dir.mkdir(parents=True)
    (data_dir / "r_articles_axe_pro.txt").write_text(
        "FOUR001;REF-1;Monture;Monture Héron;FAM;OPT;10.5\nFOUR001;REF-2;;;FAM;OPT;0\n",
        encoding="utf8",
    )

    with patched_attrs(monkeypatch, articles_fixtures, BASE_DIR=str(tmp_path)):
        articles_fixtures.import_articles()
        articles_fixtures.import_articles()

    articles = {a.reference: a for a in Article.objects.all()}
    assert set(articles) == {"REF-1", "REF-2"}
    assert articles["REF-1"].catalog_price == Decimal("10.5")
    assert articles["REF-1"].axe_pro.section == "OPT"
    assert articles["REF-2"].libelle == "REF-2"
    assert articles["REF-2"].libelle_heron == "REF-2"
    assert caplog.text.count("False") == 2


def test_article_from_article_update(make_society, make_unit, caplog):
    """Les lignes ArticleUpdate créent des articles TECH001, les doublons sont ignorés"""
    caplog.set_level(logging.INFO, logger="imports")
    make_unit(1, "U")
    tech = make_society("TECH001", is_client=False)
    ArticleUpdate.objects.create(supplier=tech, reference="R1", libelle="Un")
    ArticleUpdate.objects.create(supplier=tech, reference="R1", libelle="Un bis")

    articles_fixtures.article_from_article_update()

    assert Article.objects.filter(third_party_num="TECH001").count() == 1
    assert "True" in caplog.text


def test_main_formulaire_valide(monkeypatch, make_society, make_unit, make_big_category):
    """Avec des données valides, main() sauvegarde l'article"""
    make_society("FOUR001", is_client=False)
    make_unit(1, "U")
    category = make_big_category("Marchandises")

    with patched_attrs(
        monkeypatch,
        articles_fixtures,
        l=[
            {
                "reference": "PLV-TEST",
                "third_party_num": "FOUR001",
                "libelle": "PLV",
                "big_category": str(category.uuid_identification),
            }
        ],
    ):
        articles_fixtures.main()

    assert Article.objects.get(reference="PLV-TEST").third_party_num.third_party_num == "FOUR001"


def test_main_formulaires_invalides(caplog):
    """Les données embarquées référencent des uuid absents de la base de test : erreurs affichées"""
    caplog.set_level(logging.INFO, logger="imports")
    articles_fixtures.main()

    out = caplog.text
    assert out.count(" : ") == len(articles_fixtures.l)
    assert not Article.objects.exists()
