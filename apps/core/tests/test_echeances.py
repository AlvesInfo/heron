"""Tests du calcul des dates d'échéance selon les conditions de paiement Sage"""
import importlib
import platform
import sys
import types
from decimal import Decimal

import pytest

from apps.accountancy.models import PaymentCondition
from apps.core.bin import echeances
from apps.core.bin.echeances import get_due_date, get_payment_method_elements
from conftest import patched_attrs

pytestmark = pytest.mark.django_db


@pytest.fixture
def make_condition():
    def _factory(auuid: str, end_month="1", offset_days=30, offset_month=0):
        return PaymentCondition.objects.create(
            code=auuid, name=auuid, short_name=auuid[:20], mode="VRT", percent_at_term=Decimal("100"),
            paiement_type="VIREMENT", offset_month=offset_month, offset_days=offset_days,
            end_month=end_month, mont_echeance_min=Decimal("0"), auuid=auuid,
        )

    return _factory


@pytest.fixture(autouse=True)
def clear_cache():
    get_payment_method_elements.cache_clear()
    yield
    get_payment_method_elements.cache_clear()


def test_elements_condition_connue(make_condition):
    make_condition("C30", end_month="2", offset_days=10, offset_month=1)

    assert get_payment_method_elements("C30") == (2, 10, 1)


def test_elements_condition_inconnue():
    assert get_payment_method_elements("ABSENT") == (None, None, None)


def test_elements_end_month_null(make_condition):
    make_condition("CNULL", end_month=None)

    assert get_payment_method_elements("CNULL") == (None, 30, 0)


def test_due_date_sans_condition_fin_de_mois():
    """Tiers sans condition de paiement : plus de TypeError, échéance fin du mois de la facture"""
    assert get_due_date("2026-01-16", "ABSENT") == "2026-01-31"


@pytest.mark.parametrize(
    ("end_month", "offset_days", "offset_month", "expected"),
    [
        ("1", 0, 0, "2026-01-16"),   # départ date de facture
        ("1", 30, 0, "2026-02-15"),  # 30 jours
        ("2", 0, 1, "2026-02-28"),   # fin de mois après + 1 mois
        ("3", 10, 0, "2026-01-10"),  # fin de mois avant + 10 jours
    ],
)
def test_due_date_selon_condition(make_condition, end_month, offset_days, offset_month, expected):
    make_condition("COND", end_month=end_month, offset_days=offset_days, offset_month=offset_month)

    assert get_due_date("2026-01-16", "COND") == expected


@pytest.mark.parametrize(("node", "expected"), [("MSI", r"C:\SitesWeb\heron"), ("serveur", "/home/paulo/heron")])
def test_base_dir_selon_la_machine(monkeypatch, node, expected):
    monkeypatch.setattr(sys, "path", list(sys.path))

    try:
        with patched_attrs(monkeypatch, platform, uname=lambda: types.SimpleNamespace(node=node)):
            assert expected == importlib.reload(echeances).BASE_DIR
    finally:
        importlib.reload(echeances)
