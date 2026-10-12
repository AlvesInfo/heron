"""Tests des modèles invoices"""

import datetime

import pytest
from django.db import IntegrityError

pytestmark = pytest.mark.django_db


def test_parties_str(make_parties_invoices):
    parties = make_parties_invoices()

    assert str(parties) == f"{parties.created_at} - AF0001 - {parties.third_party_num}"


def test_invoice_str_et_unicite(make_invoice):
    invoice = make_invoice("FOUR001", invoice_number="F1", invoice_date=datetime.date(2026, 1, 31))

    assert str(invoice) == f"{invoice.third_party_num} - F1 - 2026-01-31"

    with pytest.raises(IntegrityError):
        make_invoice("FOUR001", invoice_number="F1", invoice_year=2026)


def test_sale_invoice_str_et_unicite(make_sale_invoice):
    sale = make_sale_invoice("AF0001", invoice_number="FV1")

    assert str(sale) == "FV1 - 2026-01-31 - AF0001"

    with pytest.raises(IntegrityError):
        make_sale_invoice("AF0001", invoice_number="FV1", invoice_year=2026)


def test_entete_details_str_et_ordre(make_entete_details):
    make_entete_details("Verres", ranking=2)
    make_entete_details("Montures", ranking=1)
    from apps.invoices.models import EnteteDetails

    assert [str(row) for row in EnteteDetails.objects.all()] == ["Montures", "Verres"]


def test_axes_details_unicite_axe_pro(make_axes_details):
    make_axes_details("OPT", "Montures")

    with pytest.raises(IntegrityError):
        make_axes_details("OPT", "Verres")


def test_details_cascade(make_detail, make_sale_detail):
    from apps.invoices.models import Invoice, InvoiceDetail, SaleInvoice, SaleInvoiceDetail

    detail = make_detail()
    sale_detail = make_sale_detail()
    Invoice.objects.filter(pk=detail.uuid_invoice.pk).delete()
    SaleInvoice.objects.filter(pk=sale_detail.uuid_invoice.pk).delete()

    assert InvoiceDetail.objects.count() == 0
    assert SaleInvoiceDetail.objects.count() == 0


def test_export_x3_ordre(make_export_x3, make_edi_validation):
    validation = make_edi_validation()
    first = make_export_x3(validation)
    second = make_export_x3(validation)
    from apps.invoices.models import ExportX3

    assert list(ExportX3.objects.all()) == [second, first]


def test_common_details(make_invoice_common_details):
    common = make_invoice_common_details("FOUR001", "FAC-1", final=False)

    assert common.third_party_num.third_party_num == "FOUR001"
    assert common.cct.cct == "AF0001"
