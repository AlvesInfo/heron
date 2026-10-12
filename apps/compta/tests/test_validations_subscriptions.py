"""Tests des contrôles préalables à la génération des abonnements"""
import datetime
import importlib
import platform
import sys
import types

import pytest

from apps.compta.bin import validations_subscriptions
from apps.compta.bin.validations_subscriptions import (
    get_ca_exists,
    get_have_subscriptions,
    get_missing_cosium_familly,
)
from conftest import patched_attrs

pytestmark = pytest.mark.django_db
PERIOD = ("2026-01-01", "2026-01-31")


def test_get_have_subscriptions_sans_rien():
    assert get_have_subscriptions("ROYALTIES", *PERIOD) is False


def test_get_have_subscriptions_dans_edi(make_edi_import):
    make_edi_import(flow_name="ROYALTIES", invoice_date=datetime.date(2026, 1, 10))

    assert get_have_subscriptions("ROYALTIES", *PERIOD) is True
    assert get_have_subscriptions("MEULEUSE", *PERIOD) is False
    assert get_have_subscriptions("ROYALTIES", "2026-02-01", "2026-02-28") is False


def test_get_have_subscriptions_dans_les_factures(make_invoice_with_detail):
    make_invoice_with_detail("PUBLICITE")

    assert get_have_subscriptions("PUBLICITE", *PERIOD) is True
    assert get_have_subscriptions("PRESTATIONS", *PERIOD) is False


def test_get_missing_cosium_familly(make_vente, cosium_familly_axes):
    cosium_familly_axes("LUNETTES")
    make_vente(famille_cosium="LUNETTES")
    make_vente(famille_cosium="AUDIO", rayon_cosium="AUDIO")
    make_vente(famille_cosium="LENTILLES", rayon_cosium="OPTIQUE")

    message = get_missing_cosium_familly(*PERIOD)

    assert message.startswith("Il manque des familles Cosium")
    assert "AUDIO" in message
    assert "LENTILLES" in message
    assert "LUNETTES" not in message
    assert "Paramétrage - (TIERS) Familles/Axes" in message


def test_get_missing_cosium_familly_complet(make_vente, cosium_familly_axes):
    cosium_familly_axes("LUNETTES")
    make_vente(famille_cosium="LUNETTES")

    assert get_missing_cosium_familly(*PERIOD) == ""


def test_get_ca_exists_respecte_la_periode(make_vente):
    """Les dates passées sont utilisées (elles étaient figées à janvier 2023)"""
    make_vente()

    assert get_ca_exists(*PERIOD) is True
    assert get_ca_exists("2023-01-01", "2023-01-31") is False


@pytest.mark.parametrize(("node", "expected"), [("MSI", r"C:\SitesWeb\heron"), ("serveur", "/home/paulo/heron")])
def test_base_dir_selon_la_machine(monkeypatch, node, expected):
    monkeypatch.setattr(sys, "path", list(sys.path))

    try:
        with patched_attrs(monkeypatch, platform, uname=lambda: types.SimpleNamespace(node=node)):
            assert expected == importlib.reload(validations_subscriptions).BASE_DIR
    finally:
        importlib.reload(validations_subscriptions)
