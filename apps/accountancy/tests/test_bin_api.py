# pylint: disable=E0401,W0621
"""
FR : Tests de l'API dropdown des TVA (apps/accountancy/bin/api_get_models_accountacy.py)
EN : Tests for VAT dropdown API

created at: 2026-10-10
created by: Paulo ALVES
"""
import pytest

from apps.accountancy.bin.api_get_models_accountacy import get_vat, get_vat_alls

pytestmark = pytest.mark.django_db


def test_get_vat_alls(make_vat):
    """Toutes les taxes, au format {pk, model} attendu par les dropdowns, triées par code"""
    make_vat("002", "FRA")
    make_vat("001", "FRA")
    make_vat("011", "INT")

    assert list(get_vat_alls()) == [
        {"pk": "001", "model": "001 - FRA"},
        {"pk": "002", "model": "002 - FRA"},
        {"pk": "011", "model": "011 - INT"},
    ]


@pytest.mark.parametrize(
    ("query", "expected"),
    [("int", ["011"]), ("00", ["001", "002"]), ("1|fra", ["001"]), ("zzz", []), ("", ["001", "002", "011"])],
)
def test_get_vat_recherche(make_vat, query, expected):
    """La recherche est insensible à la casse sur 'tva|régime'"""
    make_vat("001", "FRA")
    make_vat("002", "FRA")
    make_vat("011", "INT")

    assert [row["pk"] for row in get_vat(query)] == expected


def test_get_vat_sans_donnees():
    """Sans taxe en base, la recherche est vide"""
    assert not get_vat("001").exists()
