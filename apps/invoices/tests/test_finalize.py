"""Tests de la finalisation de la facturation"""
import importlib
import platform
import sys
import types

import pytest

from apps.edi.models import EdiImportControl
from apps.invoices.bin import finalize
from apps.invoices.models import Invoice, InvoiceCommonDetails, InvoiceDetail, SaleInvoice, SaleInvoiceDetail
from conftest import patched_attrs

pytestmark = pytest.mark.django_db


def test_set_validations_sans_controles_invalides(make_edi_import_control):
    make_edi_import_control(valid=True)

    finalize.set_validations()

    assert EdiImportControl.objects.count() == 1


def test_set_validations_supprime_les_orphelins_et_valide_les_autres(make_edi_import_control, make_invoice_common_details):
    orphan = make_edi_import_control(valid=False)
    used = make_edi_import_control(valid=False)
    make_invoice_common_details("FOUR001", "FAC-1", uuid_control=used)

    finalize.set_validations()

    assert not EdiImportControl.objects.filter(pk=orphan.pk).exists()
    assert EdiImportControl.objects.get(pk=used.pk).valid is True


def test_set_validations_sans_orphelin(make_edi_import_control, make_invoice_common_details):
    """Tous les contrôles invalides sont rattachés à des factures : simple validation"""
    used = make_edi_import_control(valid=False)
    make_invoice_common_details("FOUR001", "FAC-1", uuid_control=used)

    finalize.set_validations()

    assert EdiImportControl.objects.get(pk=used.pk).valid is True


def test_finalize_global_invoices(make_user, make_detail, make_sale_detail, make_invoice_common_details):
    user = make_user()
    make_detail()
    make_sale_detail()
    make_invoice_common_details(final=False)

    finalize.finalize_global_invoices(user)

    for model in (Invoice, InvoiceDetail, InvoiceCommonDetails, SaleInvoice, SaleInvoiceDetail):
        row = model.objects.get()
        assert row.final is True
        assert row.final_at is not None
        assert row.modified_by == user


def test_finalize_emails_et_export(make_sale_detail, make_detail, make_invoice_common_details):
    make_sale_detail()
    make_detail()
    make_invoice_common_details()

    finalize.finalize_emails_invoices()
    finalize.finalize_export_invoices()

    assert SaleInvoice.objects.get().send_email is True
    for model in (Invoice, InvoiceDetail, InvoiceCommonDetails, SaleInvoice, SaleInvoiceDetail):
        assert model.objects.get().export is True


def test_finalize_cct_email_invoice(make_sale_invoice):
    paris = make_sale_invoice("AF0001")
    lyon = make_sale_invoice("AF0002")

    finalize.finalize_cct_email_invoice("AF0001")

    paris.refresh_from_db()
    lyon.refresh_from_db()
    assert paris.final is True
    assert paris.send_email is True
    assert lyon.final is False
    assert lyon.send_email is False


@pytest.mark.parametrize(("node", "expected"), [("MSI", "/"), ("serveur", "/home/paulo/heron")])
def test_base_dir_selon_la_machine(monkeypatch, node, expected):
    monkeypatch.setattr(sys, "path", list(sys.path))

    try:
        with patched_attrs(monkeypatch, platform, uname=lambda: types.SimpleNamespace(node=node)):
            assert expected == importlib.reload(finalize).BASE_DIR
    finally:
        importlib.reload(finalize)
