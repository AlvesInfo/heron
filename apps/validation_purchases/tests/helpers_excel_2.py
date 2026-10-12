# pylint: disable=E0401,W0621,C0415
"""FR : Fabriques des tests des exports Excel (CA, fournisseurs M/M-1, RFA, achats) de


     validation_purchases. Importées explicitement : `from ...helpers_excel_2 import *`
EN : Fixtures for validation_purchases Excel exports tests
"""

import datetime
from collections.abc import Callable
from decimal import Decimal
from typing import Any
from uuid import uuid4

import pendulum
import pytest

from conftest import next_code

# Mois M (mois précédent) et M-1 (deux mois avant), au sens des requêtes SQL (date_trunc(now()))
MONTH_M = pendulum.now().subtract(months=1).start_of("month").date()
MONTH_M1 = pendulum.now().subtract(months=2).start_of("month").date()


@pytest.fixture
def make_ca_client(make_maison, make_section) -> Callable[..., Any]:
    """Fabrique de compta.CaClients (CA Cosium par maison et axe pro)"""
    from apps.compta.models import CaClients

    def _factory(maison=None, axe_pro=None, **kwargs: Any):
        defaults = {
            "date_ca": MONTH_M,
            "cct_uuid_identification": maison or make_maison(),
            "axe_pro": axe_pro or make_section("PRO", "OPT"),
            "famille_cosium": "LUNETTES",
            "ca_ht_eur": Decimal(50),
            "ca_ht_devise": Decimal(50),
        }
        defaults.update(kwargs)
        defaults.setdefault("code_maison", defaults["cct_uuid_identification"].cct.cct)
        defaults.setdefault("code_cosium", "COS1")
        return CaClients.objects.create(**defaults)

    return _factory


@pytest.fixture
def make_sale_invoice(make_society, make_cct) -> Callable[..., Any]:
    """Fabrique minimale de invoices.SaleInvoice (vente type_x3 1)"""
    from apps.invoices.models import SaleInvoice

    def _factory(cct=None, invoice_month: datetime.date = MONTH_M, **kwargs: Any):
        defaults = {
            "invoice_sage_number": next_code("VTE"),
            "invoice_number": next_code("FV"),
            "invoice_date": invoice_month,
            "invoice_month": invoice_month,
            "invoice_year": invoice_month.year,
            "invoice_type": "380",
            "invoice_type_name": "Facture",
            "invoice_amount_without_tax": Decimal(100),
            "invoice_amount_tax": Decimal(20),
            "invoice_amount_with_tax": Decimal(120),
            "big_category": "Marchandises",
            "big_category_code": "MAR",
            "big_category_slug_name": "marchandises",
            "big_category_ranking": 1,
            "formation": "",
            "type_x3": 1,
        }
        defaults.update(kwargs)
        return SaleInvoice.objects.create(
            cct=cct or make_cct("AF0001"), third_party_num=make_society("CLI001"), **defaults
        )

    return _factory


@pytest.fixture
def make_sale_invoice_detail(make_sale_invoice) -> Callable[..., Any]:
    """Fabrique minimale de invoices.SaleInvoiceDetail"""
    from apps.invoices.models import SaleInvoiceDetail

    def _factory(sale_invoice=None, **kwargs: Any):
        defaults = {
            "import_uuid_identification": uuid4(),
            "axe_bu": "CAHA",
            "axe_prj": "NAF",
            "axe_pro": "OPT",
            "axe_rfa": "NAF",
            "axe_pys": "FR",
            "vat": "001",
            "vat_rate": Decimal("0.2"),
            "vat_regime": "FRA",
            "big_category": "Marchandises",
            "base": "Marchandises",
            "account": "707000",
            "account_od_600": "607000",
            "net_amount": Decimal(100),
        }
        defaults.update(kwargs)
        return SaleInvoiceDetail.objects.create(
            uuid_invoice=sale_invoice or make_sale_invoice(), **defaults
        )

    return _factory


@pytest.fixture
def make_purchase_invoice_2(make_society, make_invoice_common_details) -> Callable[..., Any]:
    """Fabrique d'une facture d'achat complète : invoices.Invoice + InvoiceDetail + InvoiceCommonDetails

    liés par import_uuid_identification, pour le cct donné. Renvoie (invoice, detail, common).
    """
    from apps.invoices.models import Invoice, InvoiceDetail

    def _factory(
        cct,
        third_party_num: str = "FOUR001",
        integration_month: datetime.date = MONTH_M1,
        final: bool = True,
        net_amount=Decimal(80),
        **kwargs: Any,
    ):
        society = make_society(third_party_num, is_client=False)
        invoice = Invoice.objects.create(
            third_party_num=society,
            invoice_sage_number=next_code("ACH"),
            invoice_number=next_code("FAC"),
            invoice_date=integration_month,
            invoice_month=integration_month,
            invoice_year=integration_month.year,
            integration_month=integration_month,
            invoice_type="380",
            final=final,
            invoice_amount_without_tax=net_amount,
            invoice_amount_tax=Decimal(0),
            invoice_amount_with_tax=net_amount,
            **kwargs,
        )
        import_uuid = uuid4()
        detail = InvoiceDetail.objects.create(
            uuid_invoice=invoice,
            import_uuid_identification=import_uuid,
            axe_bu="CAHA",
            axe_prj="NAF",
            axe_pro="OPT",
            axe_rfa="NAF",
            axe_pys="FR",
            vat="001",
            vat_rate=Decimal("0.2"),
            vat_regime="FRA",
            big_category="Marchandises",
            account="607000",
            net_amount=net_amount,
            gross_amount=net_amount,
        )
        common = make_invoice_common_details(
            third_party_num,
            invoice.invoice_number,
            import_uuid_identification=import_uuid,
            cct=cct,
            invoice_date=integration_month,
            invoice_year=integration_month.year,
            final=final,
            reference_article="ART-1",
            libelle="Article 1",
            qty=Decimal(1),
        )
        return invoice, detail, common

    return _factory


@pytest.fixture
def make_supplier_rate(make_society) -> Callable[..., Any]:
    """Fabrique de rfa.SupplierRate (taux de RFA d'un fournisseur)"""
    from apps.rfa.models import SupplierRate

    def _factory(third_party_num: str = "FOUR001", rate=Decimal("0.05")):
        return SupplierRate.objects.create(
            supplier=make_society(third_party_num, is_client=False), rfa_rate=rate
        )

    return _factory


def excel_values(read, file_io, column: int):
    """Valeurs non vides d'une colonne de la première feuille"""
    return [
        row[column] for row in read(file_io) if len(row) > column and row[column] not in (None, "")
    ]
