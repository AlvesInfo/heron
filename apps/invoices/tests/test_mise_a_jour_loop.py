"""Tests de la mise à jour des éléments figés pour la facturation (centrales, enseignes, parties)"""

import importlib
import platform
import sys
import types

import pytest

from apps.data_flux.models import Trace
from apps.invoices.loops import mise_a_jour_loop
from apps.invoices.models import CentersInvoices, PartiesInvoices, SignboardsInvoices
from conftest import patched_attrs

pytestmark = pytest.mark.django_db


def test_centers_invoices_update(make_child_center):
    make_child_center("ACF", comment="Commentaire", member_num="12345")

    trace = mise_a_jour_loop.centers_invoices_update()

    center = CentersInvoices.objects.get()
    assert center.code_center == "ACF"
    assert center.member_num == "12345"
    assert center.vat_regime_center == "FRA"
    assert trace.created_numbers_records == 1

    # Relance sans changement : la ligne existante est réutilisée (même uuid)
    mise_a_jour_loop.centers_invoices_update()
    assert CentersInvoices.objects.count() == 1


def test_signboards_invoices_update(make_signboard):
    make_signboard("ACF", message="Bienvenue")

    mise_a_jour_loop.signboards_invoices_update()
    mise_a_jour_loop.signboards_invoices_update()

    signboard = SignboardsInvoices.objects.get()
    assert signboard.code_signboard == "ACF"
    assert signboard.message == "Bienvenue"


def test_parties_invoices_update(make_maison, make_society, make_country):
    client = make_society(
        "CLI001",
        invoice_entete="",
        immeuble="NONE",
        adresse="2 avenue",
        ville="Paris",
        pays=make_country("FR", "France"),
    )
    maison = make_maison("AF0001", third_party_num=client, immeuble=None, invoice_entete="")

    trace = mise_a_jour_loop.parties_invoices_update()

    parties = PartiesInvoices.objects.get()
    assert parties.cct == maison.cct
    assert parties.third_party_num == client
    assert parties.pays_cct == "France"
    assert parties.immeuble_cct == ""
    assert parties.name_third_party == client.name
    assert parties.immeuble_third_party == ""
    assert trace.created_numbers_records == 1
    client.refresh_from_db()
    maison.refresh_from_db()
    assert client.invoice_entete == client.name
    assert client.immeuble == ""
    assert maison.invoice_entete == maison.intitule
    assert maison.immeuble == ""


def test_process_update(make_child_center, make_signboard, make_maison):
    make_child_center("ACF")
    make_signboard("ACF")
    make_maison("AF0001")

    mise_a_jour_loop.process_update()

    assert CentersInvoices.objects.count() == 1
    assert SignboardsInvoices.objects.count() == 1
    assert PartiesInvoices.objects.count() == 1
    assert Trace.objects.filter(errors=False).count() == 3


def test_process_update_erreur(monkeypatch, caplog):
    """Une exception dans un traitement est tracée et n'empêche pas les suivants"""
    trace_holder = {}

    def failing():
        trace_holder["trace"] = Trace.objects.create(
            trace_name="t", comment="init", created_numbers_records=0
        )
        raise RuntimeError("boom")

    with (
        patched_attrs(
            monkeypatch,
            mise_a_jour_loop,
            centers_invoices_update=failing,
            signboards_invoices_update=lambda: None,
            parties_invoices_update=lambda: None,
        ),
        caplog.at_level("ERROR", logger="imports"),
    ):
        mise_a_jour_loop.process_update()

    assert "boom" in caplog.text
    # la trace créée dans le traitement n'est pas renvoyée : elle reste sans erreur (comportement du code)
    assert Trace.objects.get(pk=trace_holder["trace"].pk).errors is False


@pytest.mark.parametrize(("node", "expected"), [("MSI", "/"), ("serveur", "/home/paulo/heron")])
def test_base_dir_selon_la_machine(monkeypatch, node, expected):
    monkeypatch.setattr(sys, "path", list(sys.path))

    try:
        with patched_attrs(monkeypatch, platform, uname=lambda: types.SimpleNamespace(node=node)):
            assert expected == importlib.reload(mise_a_jour_loop).BASE_DIR
    finally:
        importlib.reload(mise_a_jour_loop)
