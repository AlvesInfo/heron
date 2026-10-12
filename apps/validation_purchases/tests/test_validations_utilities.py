"""Tests des utilitaires de validation (multi-magasins, identifiants fournisseurs, traces, période)"""

import datetime
import logging

import pytest

from apps.data_flux.models import Trace
from apps.edi.models import EdiImport, EdiValidation
from apps.validation_purchases.bin import validations_utilities
from apps.validation_purchases.bin.validations_utilities import (
    create_edi_validation,
    flag_invoices,
    set_is_multi_store,
    verify_supplier_ident,
)
from conftest import patched_attrs

pytestmark = pytest.mark.django_db


def test_set_is_multi_store(make_edi_import, make_maison):
    paris, lyon = make_maison("AF0001"), make_maison("AF0002")
    mono = make_edi_import(invoice_number="F1", invoice_year=2026, cct_uuid_identification=paris)
    make_edi_import(invoice_number="F1", invoice_year=2026, cct_uuid_identification=paris)
    multi_a = make_edi_import(invoice_number="F2", invoice_year=2026, cct_uuid_identification=paris)
    multi_b = make_edi_import(invoice_number="F2", invoice_year=2026, cct_uuid_identification=lyon)

    set_is_multi_store("FOUR001", "F1", 2026)
    set_is_multi_store("FOUR001", "F2", 2026)

    assert EdiImport.objects.get(pk=mono.pk).is_multi_store is False
    assert EdiImport.objects.get(pk=multi_a.pk).is_multi_store is True
    assert EdiImport.objects.get(pk=multi_b.pk).is_multi_store is True


def test_verify_supplier_ident(make_edi_import, make_trace):
    """Un import sans identifiant fournisseur est supprimé et sa trace dupliquée en erreur"""
    trace = make_trace(file_name="widex.csv", invoices=False)
    bad = make_edi_import(uuid_identification=trace.uuid_identification, supplier_ident="")
    good = make_edi_import(supplier_ident="widex")

    verify_supplier_ident()

    assert not EdiImport.objects.filter(pk=bad.pk).exists()
    assert EdiImport.objects.filter(pk=good.pk).exists()
    copies = Trace.objects.filter(file_name="widex.csv").order_by("pk")
    assert copies.count() == 2
    new_trace = copies.last()
    assert new_trace.errors is True
    assert new_trace.invoices is True
    assert "ne contenait pas l'identifiant du fournisseur" in new_trace.comment
    assert new_trace.uuid_identification != trace.uuid_identification


def test_flag_invoices(make_edi_import, make_trace):
    linked = make_trace(invoices=False)
    other = make_trace(invoices=False)
    make_edi_import(uuid_identification=linked.uuid_identification)

    flag_invoices()

    linked.refresh_from_db()
    other.refresh_from_db()
    assert linked.invoices is True
    assert other.invoices is False


def test_create_edi_validation_existante(make_edi_validation):
    validation = make_edi_validation(billing_period=datetime.date(2026, 1, 1))
    make_edi_validation(billing_period=datetime.date(2025, 12, 1), final=True)

    assert create_edi_validation() == validation.uuid_identification
    assert EdiValidation.objects.count() == 2


def test_create_edi_validation_creee():
    identification = create_edi_validation()

    validation = EdiValidation.objects.get()
    assert identification == validation.uuid_identification
    assert validation.billing_period == datetime.date.today()
    assert validation.final is False


def test_create_edi_validation_erreur(monkeypatch, caplog):
    def boom(**kwargs):
        raise RuntimeError("boom")

    with (
        patched_attrs(monkeypatch, validations_utilities.EdiValidation.objects, get_or_create=boom),
        caplog.at_level(logging.ERROR, logger="edi"),
    ):
        assert create_edi_validation() is None

    assert "create_edi_validation" in caplog.text
