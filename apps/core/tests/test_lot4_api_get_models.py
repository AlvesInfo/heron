# pylint: disable=E0401,W0621
"""
FR : Tests des requêtes des api de listes déroulantes (apps/core/bin/api_get_models.py)
EN : Tests for dropdown api queries

created at: 2026-10-11
created by: Paulo ALVES
"""
import datetime

import pytest

from apps.core.bin import api_get_models

pytestmark = pytest.mark.django_db


@pytest.fixture
def catalogue(make_society, make_article):
    """Deux fournisseurs, dont un multi facturant, avec leurs articles"""
    mono = make_society("FOUR001", name="Mono", is_client=False, is_multi_billing=False)
    multi = make_society("FOUR002", name="Multi", is_client=False, is_multi_billing=True)
    make_article("MONT-1", society=mono, ean_code="123", libelle="Monture", libelle_heron="Monture Héron")
    make_article("VERRE-1", society=mono, libelle="Verre", libelle_heron="")
    make_article("MONT-2", society=multi, libelle="Monture multi", libelle_heron=None)
    return {"mono": mono, "multi": multi}


def _models(rows):
    return sorted(row["model"] for row in rows)


def test_articles_alls_et_libelle_heron_par_defaut(catalogue):
    """Tous les articles, libellé héron s'il est renseigné sinon libellé fournisseur"""
    rows = list(api_get_models.get_articles_alls())

    assert _models(rows) == ["FOUR001 - MONT-1 - Monture Héron", "FOUR001 - VERRE-1 - Verre", "FOUR002 - MONT-2 - Monture multi"]
    assert set(rows[0]) == {"pk", "model"}
    assert _models(api_get_models.get_articles_alls("FOUR002")) == ["FOUR002 - MONT-2 - Monture multi"]


def test_articles_recherche_filtree_par_tiers_non_multi_facturant(catalogue):
    """Un tiers non multi facturant ne voit que ses articles ; un multi facturant voit tout"""
    assert _models(api_get_models.get_articles("mont")) == ["FOUR001 - MONT-1 - Monture Héron", "FOUR002 - MONT-2 - Monture multi"]
    assert _models(api_get_models.get_articles("mont", "FOUR001")) == ["FOUR001 - MONT-1 - Monture Héron"]
    assert _models(api_get_models.get_articles("mont", "FOUR002")) == ["FOUR001 - MONT-1 - Monture Héron", "FOUR002 - MONT-2 - Monture multi"]
    assert _models(api_get_models.get_articles("123")) == ["FOUR001 - MONT-1 - Monture Héron"]
    assert _models(api_get_models.get_articles("mont", "ABSENT")) == ["FOUR001 - MONT-1 - Monture Héron", "FOUR002 - MONT-2 - Monture multi"]


def test_societies(make_society, make_country):
    make_society("TIERS01", name="Acuitis", ville="Paris", country=make_country("FR", "France"))
    make_society("TIERS02", name="Autre", ville="Lyon")

    rows = list(api_get_models.get_societies_alls())
    found = list(api_get_models.get_societies("paris"))

    assert {row["pk"] for row in rows} == {"TIERS01", "TIERS02"}
    assert found == [{"pk": "TIERS01", "model": "TIERS01 - Acuitis - Paris - France"}]
    assert list(api_get_models.get_societies("inconnu")) == []


def test_maisons(make_maison, make_cct):
    make_cct("AF0001", active=True)
    opened = make_maison("AF0001", intitule="Paris", ville="Paris", adresse="1 rue")
    make_maison("AF0002", intitule="Lyon", ville="Lyon", adresse="2 rue", closing_date=datetime.date(2025, 1, 1))
    make_cct("AF0003", active=False)
    make_maison("AF0003", intitule="Nice", ville="Nice", adresse="3 rue")

    assert [row["model"] for row in api_get_models.get_maisons("paris")] == ["AF0001 - Paris - 1 rue - Paris"]
    assert next(iter(api_get_models.get_maisons("paris")))["pk"] == opened.uuid_identification
    assert sorted(row["model"][:6] for row in api_get_models.get_maisons_alls()) == ["AF0001", "AF0002", "AF0003"]
    assert sorted(row["model"][:6] for row in api_get_models.get_maisons("af000")) == ["AF0001", "AF0002", "AF0003"]
    assert sorted(row["model"][:6] for row in api_get_models.get_maisons_in_use("af000")) == ["AF0001", "AF0003"]
    assert [row["pk"] for row in api_get_models.get_cct_in_use_active("af000")] == ["AF0001"]


def test_unites(make_unit):
    make_unit(1, "Unité")
    make_unit(2, "Kilo")

    assert list(api_get_models.get_unity_alls()) == [{"num": 1, "unity": "Unité"}, {"num": 2, "unity": "Kilo"}]
    assert list(api_get_models.get_unity("kil")) == [{"num": 2, "unity": "Kilo"}]


def test_comptes(make_account):
    account = make_account("FRA", "411000")
    make_account("FRA", "607000")

    rows = list(api_get_models.get_account("411"))

    assert rows == [{"pk": account.uuid_identification, "model": "411000 - FRA"}]
    assert len(list(api_get_models.get_accounts_alls())) == 2
