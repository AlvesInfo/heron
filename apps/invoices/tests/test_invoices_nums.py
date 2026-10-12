"""Tests de la numérotation des factures et des fichiers d'export"""

import pendulum
import pytest

from apps.invoices.bin import invoives_nums

pytestmark = pytest.mark.django_db


def test_get_invoice_num_prefixe_date(make_counter):
    make_counter("invoices_num", num=7, prefix="AAAAMM", lpad_num=5)

    assert invoives_nums.get_invoice_num(pendulum.date(2026, 1, 31)) == "20260100007"
    assert invoives_nums.get_invoice_num(pendulum.date(2026, 1, 31)) == "20260100008"


@pytest.mark.parametrize(
    ("function", "counter"),
    [
        (invoives_nums.get_purchase_num, "purchase_num"),
        (invoives_nums.get_bicpar_num, "bicpar_num"),
        (invoives_nums.get_bispar_num, "bispar_num"),
        (invoives_nums.get_bispard_num, "bispard_num"),
        (invoives_nums.get_gaspar_num, "gaspar_num"),
        (invoives_nums.get_bispa_num, "bispa_num"),
    ],
)
def test_compteurs_simples(make_counter, function, counter):
    make_counter(counter, num=3, lpad_num=4)

    assert function() == "0003"
    assert function() == "0004"


def test_get_zip_num(make_counter, monkeypatch):
    make_counter("generic", num=12, lpad_num=4)
    monkeypatch.setattr(
        invoives_nums.pendulum, "now", lambda *a, **k: pendulum.datetime(2026, 1, 31)
    )

    assert invoives_nums.get_zip_num() == "ZIP_2026_01_31_0012"
