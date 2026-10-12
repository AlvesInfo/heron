# pylint: disable=E0401,W0621
"""
FR : Tests des requêtes SQL de taux de TVA (apps/accountancy/bin/utilities.py)
EN : Tests for VAT rate SQL queries

created at: 2026-10-10
created by: Paulo ALVES
"""
import datetime
from decimal import Decimal

import pytest

from apps.accountancy.bin.utilities import get_dict_vat_rates, get_vat_rate, get_youngests_vat_rate

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    ("invoice_date", "vat", "expected"),
    [
        ("2023-01-01", "001", ("FRA", Decimal("0.20000"))),
        ("2014-01-01", "001", ("FRA", Decimal("0.20000"))),
        ("2013-12-31", "001", ("FRA", Decimal("0.19600"))),
        ("2023-01-01", "002", ("FRA", Decimal("0.05500"))),
        ("2023-01-01", "011", ("INT", Decimal("0.20000"))),
        ("2023-01-01", "999", None),
        ("1999-12-31", "001", None),
    ],
)
@pytest.mark.usefixtures('vat_rates_dataset')
def test_get_vat_rate(invoice_date, vat, expected):
    """Le taux retourné est celui dont la date de début est la plus récente avant la facture"""
    assert get_vat_rate(invoice_date, vat) == expected


@pytest.mark.usefixtures('vat_rates_dataset')
def test_get_vat_rate_accepte_une_date():
    """La date peut être passée en objet date"""
    assert get_vat_rate(datetime.date(2010, 6, 1), "001") == ("FRA", Decimal("0.19600"))


@pytest.mark.usefixtures('vat_rates_dataset')
def test_get_dict_vat_rates():
    """Dictionnaire {tva: (régime, taux)} à la date de la facture"""
    rates = get_dict_vat_rates("2023-01-01")

    assert set(rates) == {"001", "002", "011"}
    assert rates["001"] == ("FRA", Decimal("0.2"))
    assert rates["002"] == ("FRA", Decimal("0.055"))
    assert rates["011"] == ("INT", Decimal("0.2"))


@pytest.mark.usefixtures('vat_rates_dataset')
def test_get_dict_vat_rates_historique():
    """Avant 2014, la 001 est à 19.6 % et la 011 n'existe pas encore"""
    rates = get_dict_vat_rates("2010-01-01")

    assert rates == {"001": ("FRA", Decimal("0.196")), "002": ("FRA", Decimal("0.055"))}


@pytest.mark.usefixtures('vat_rates_dataset')
def test_get_youngests_vat_rate():
    """Taux en cours triés par code tva : (tva, taux, régime)"""
    assert get_youngests_vat_rate() == [
        ("001", Decimal("0.20000"), "FRA"),
        ("002", Decimal("0.05500"), "FRA"),
        ("011", Decimal("0.20000"), "INT"),
    ]


def test_sans_taux_en_base():
    """Sans données : résultats vides"""
    assert get_vat_rate("2023-01-01", "001") is None
    assert get_dict_vat_rates("2023-01-01") == {}
    assert get_youngests_vat_rate() == []
