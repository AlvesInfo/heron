# pylint: disable=E0401,W0621
"""FR : Tests du calcul des échéances (apps/accountancy/bin/utils.py)


EN : Tests for due dates computation

created at: 2026-10-10
created by: Paulo ALVES
"""

import datetime
from decimal import Decimal

import pytest

from apps.accountancy.bin.utils import due_date_calculate, get_str_echeances
from apps.accountancy.models import PaymentCondition


def _condition(end_month, offset_month, offset_days):
    return PaymentCondition(
        code="X", end_month=end_month, offset_month=offset_month, offset_days=offset_days
    )


@pytest.mark.parametrize(
    ("invoice_date", "end_month", "offset_month", "offset_days", "expected"),
    [
        (datetime.date(2024, 1, 15), "1", 0, 0, "15/01/2024"),
        (datetime.date(2024, 1, 15), "1", 0, 30, "14/02/2024"),
        (datetime.date(2024, 1, 31), "1", 0, 45, "16/03/2024"),
        (datetime.date(2024, 1, 15), "2", 0, 0, "31/01/2024"),
        (datetime.date(2024, 1, 15), "2", 1, 0, "29/02/2024"),
        (datetime.date(2024, 1, 15), "2", 1, 10, "10/03/2024"),
        (datetime.date(2024, 3, 15), "3", 0, 0, "29/02/2024"),
        (datetime.date(2024, 3, 15), "3", 2, 0, "30/04/2024"),
        (datetime.date(2024, 1, 15), "1", 1, 0, "29/02/2024"),
        (datetime.date(2023, 12, 31), "2", 1, 0, "31/01/2024"),
        (datetime.date(2024, 1, 15), None, None, None, "15/01/2024"),
        (datetime.datetime(2024, 1, 15, 10, 30), "1", 0, 1, "16/01/2024"),
    ],
)
def test_due_date_calculate(invoice_date, end_month, offset_month, offset_days, expected):
    """end_month : 1 = non, 2 = fin de mois après, 3 = fin de mois avant ;

    un décalage en mois se termine toujours en fin de mois ; les jours s'ajoutent ensuite
    """
    assert (
        due_date_calculate(invoice_date, _condition(end_month, offset_month, offset_days))
        == expected
    )


def test_due_date_calculate_offsets_en_texte():
    """Les décalages peuvent arriver sous forme de chaînes (int() est appliqué)"""
    assert due_date_calculate(datetime.date(2024, 1, 15), _condition("1", "1", "5")) == "05/03/2024"


@pytest.mark.django_db
def test_get_str_echeances_multiples(make_payment_condition):
    """Les échéances partielles affichent leur pourcentage, triées par mois puis jours"""
    make_payment_condition(
        "3070", percent_at_term=Decimal(70), offset_month=1, offset_days=0, end_month="2"
    )
    make_payment_condition(
        "3070", percent_at_term=Decimal(30), offset_month=0, offset_days=30, end_month="1"
    )
    make_payment_condition("AUTRE", percent_at_term=Decimal(100), offset_days=60)

    assert (
        get_str_echeances(datetime.date(2024, 1, 15), "3070")
        == "30 % le 14/02/2024, 70 % le 29/02/2024"
    )


@pytest.mark.parametrize("percent", [Decimal(100), Decimal(0)])
@pytest.mark.django_db
def test_get_str_echeances_sans_pourcentage(make_payment_condition, percent):
    """100 % ou 0 % : pas de préfixe de pourcentage"""
    make_payment_condition("30J", percent_at_term=percent, offset_days=30)

    assert get_str_echeances(datetime.date(2024, 1, 15), "30J") == "14/02/2024"


@pytest.mark.django_db
def test_get_str_echeances_code_inconnu(make_payment_condition):
    """Aucune condition : chaîne vide"""
    make_payment_condition("30J")

    assert get_str_echeances(datetime.date(2024, 1, 15), "INCONNU") == ""
