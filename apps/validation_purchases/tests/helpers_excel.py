# pylint: disable=E0401,W0621,C0415,R0913
"""FR : Aides des tests des exports Excel de validation_purchases (chantier VP-A1).


     Importées explicitement : `from apps.validation_purchases.tests.helpers_excel import ...`
EN : Helpers for validation_purchases Excel exports tests
"""

import datetime
import io
from collections.abc import Callable
from decimal import Decimal
from typing import Any
from uuid import uuid4

import pendulum
import pytest
from django.db import connection

from apps.core.excel_outputs import generic_list_export
from conftest import next_code

KO = {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}


def month_ago(months: int) -> datetime.date:
    """Premier jour du mois courant moins `months` mois (référence des SQL basées sur now())"""
    return pendulum.now().start_of("month").subtract(months=months).date()


def boom(*_args, **_kwargs):
    """Fonction qui lève : branche except des exports"""
    raise ValueError("boom")


def run_export(function, *args) -> tuple[dict, io.BytesIO]:
    """Exécute un export en mémoire et renvoie (résultat, flux)"""
    file_io = io.BytesIO()
    result = function(file_io, *args)
    return result, file_io


def cells(rows, value) -> bool:
    """True si une cellule de la feuille vaut `value`"""
    return any(cell == value for row in rows for cell in row)


@pytest.fixture
def ko_writer(monkeypatch) -> Callable[[Any], None]:
    """Fait lever titre_page_writer du module d'export passé en paramètre"""

    def _patch(module) -> None:
        monkeypatch.setattr(generic_list_export, "titre_page_writer", boom)
        monkeypatch.setattr(module, "titre_page_writer", boom, raising=False)

    return _patch


@pytest.fixture
def make_edi_row(make_edi_import, make_maison, make_icon_origin, make_section, make_big_category):
    """Ligne edi_ediimport valide et complète pour les écrans de validation : maison rattachée

    (sauf cct=None), origine, axes, catégorie, mois de facturation janvier 2026 par défaut.
    """
    make_icon_origin(1, "EDI", "file")

    def _factory(
        third_party_num: str = "FOUR001", maison=None, cct: str | None = "AF0001", **kwargs: Any
    ):
        from apps.centers_clients.models import Maison

        if maison is None and cct is not None:
            maison = Maison.objects.filter(cct__cct=cct).first() or make_maison(cct)

        invoice_date = kwargs.pop("invoice_date", datetime.date(2026, 1, 15))
        defaults = {
            "supplier": "FOURNISSEUR 1",
            "flow_name": "Widex",
            "invoice_date": invoice_date,
            "invoice_month": invoice_date.replace(day=1),
            "invoice_year": invoice_date.year,
            "invoice_type": "380",
            "devise": "EUR",
            "purchase_invoice": True,
            "sale_invoice": False,
            "cct_uuid_identification": maison,
            "origin": make_icon_origin(1, "EDI", "file"),
            "axe_bu": make_section("BU", "CAHA"),
            "axe_prj": make_section("PRJ", "NAF"),
            "axe_pro": make_section("PRO", "OPT"),
            "axe_pys": make_section("PYS", "FR"),
            "axe_rfa": make_section("RFA", "NAF"),
            "big_category": make_big_category("Marchandises"),
            "net_amount": Decimal(100),
            "net_unit_price": Decimal(100),
            "gross_unit_price": Decimal(120),
            "invoice_amount_without_tax": Decimal(100),
            "invoice_amount_tax": Decimal(20),
            "invoice_amount_with_tax": Decimal(120),
            "vat_rate": Decimal("0.2"),
            "vat_amount": Decimal(20),
            "amount_with_vat": Decimal(120),
            "is_multi_store": False,
            "code_maison": cct or "",
            "maison": f"Maison {cct}" if cct else "",
        }
        defaults.update(kwargs)
        return make_edi_import(third_party_num=third_party_num, **defaults)

    return _factory


@pytest.fixture
def make_purchase_invoice(make_society, make_invoice_common_details):
    """Facture d'achat définitive (invoices.Invoice final/export + InvoiceDetail + InvoiceCommonDetails

    reliés par import_uuid_identification) pour un mois d'intégration donné.
    """
    from apps.invoices.models import Invoice, InvoiceDetail

    def _factory(
        third_party_num: str = "FOUR001",
        integration_month: datetime.date | None = None,
        net_amount=Decimal(50),
        cct: str = "AF0001",
        flow_name: str = "Widex",
        axe_pro: str = "OPT",
        **kwargs: Any,
    ):
        integration_month = integration_month or month_ago(1)
        society = make_society(third_party_num, is_client=False)
        invoice = Invoice.objects.create(
            third_party_num=society,
            invoice_sage_number=next_code("ACH"),
            invoice_number=next_code("FAC"),
            invoice_date=integration_month,
            invoice_month=integration_month,
            invoice_year=integration_month.year,
            integration_month=integration_month,
            final=True,
            export=True,
            **kwargs,
        )
        import_uuid = uuid4()
        detail = InvoiceDetail.objects.create(
            uuid_invoice=invoice,
            import_uuid_identification=import_uuid,
            axe_bu="CAHA",
            axe_prj="NAF",
            axe_pro=axe_pro,
            axe_rfa="NAF",
            axe_pys="FR",
            vat="001",
            vat_rate=Decimal("0.2"),
            vat_regime="FRA",
            big_category="Marchandises",
            account="607000",
            flow_name=flow_name,
            net_amount=net_amount,
        )
        common = make_invoice_common_details(
            third_party_num,
            invoice.invoice_number,
            import_uuid_identification=import_uuid,
            cct=__import__("apps.accountancy.models", fromlist=["CctSage"]).CctSage.objects.get(
                cct=cct
            ),
            invoice_date=integration_month,
            invoice_year=integration_month.year,
            flow_name=flow_name,
            reference_article="ART-1",
        )
        return invoice, detail, common

    return _factory


@pytest.fixture
def make_sale_rows(make_society, make_cct, make_invoice_common_details):
    """Facture de vente définitive (SaleInvoice final + SaleInvoiceDetail + InvoiceCommonDetails)"""
    from apps.invoices.models import SaleInvoice, SaleInvoiceDetail

    def _factory(
        cct: str = "AF0001",
        third_party_num: str = "CLI001",
        invoice_month: datetime.date | None = None,
        net_amount=Decimal(30),
        flow_name: str = "ROYALTIES",
    ):
        invoice_month = invoice_month or month_ago(2)
        cct_obj = make_cct(cct)
        society = make_society(third_party_num)
        sale = SaleInvoice.objects.create(
            cct=cct_obj,
            third_party_num=society,
            invoice_sage_number=next_code("VTE"),
            invoice_number=next_code("FV"),
            invoice_date=invoice_month,
            invoice_month=invoice_month,
            invoice_year=invoice_month.year,
            invoice_type="380",
            invoice_type_name="Facture",
            big_category="Abonnements",
            big_category_code="ABO",
            big_category_slug_name="abonnements",
            big_category_ranking=1,
            formation="",
            type_x3=1,
            final=True,
        )
        import_uuid = uuid4()
        SaleInvoiceDetail.objects.create(
            uuid_invoice=sale,
            import_uuid_identification=import_uuid,
            axe_bu="CAHA",
            axe_prj="NAF",
            axe_pro="OPT",
            axe_rfa="NAF",
            axe_pys="FR",
            vat="001",
            vat_rate=Decimal("0.2"),
            vat_regime="FRA",
            big_category="Abonnements",
            base="Abonnements",
            account="706000",
            account_od_600="606000",
            net_amount=net_amount,
        )
        make_invoice_common_details(
            third_party_num,
            sale.invoice_number,
            import_uuid_identification=import_uuid,
            cct=cct_obj,
            invoice_date=invoice_month,
            invoice_year=invoice_month.year,
            flow_name=flow_name,
            reference_article="ROY",
        )
        return sale

    return _factory


@pytest.fixture
def make_subscription(
    make_maison, make_article, make_society, make_invoice_function, make_unit, make_vat
):
    """Abonnement d'une maison (centers_clients.MaisonSubcription) pour une fonction de facturation"""
    from apps.centers_clients.models import MaisonSubcription

    def _factory(maison=None, function_name: str = "ROYALTIES"):
        from apps.articles.models import Article

        society = make_society("ZROYAL")
        article = Article.objects.filter(
            third_party_num=society, reference="ROY"
        ).first() or make_article(reference="ROY", society=society)
        return MaisonSubcription.objects.create(
            maison=maison or make_maison("AF0001"),
            article=article,
            qty=Decimal(1),
            unit_weight=make_unit(1, "U"),
            function=make_invoice_function(
                function_name, function=f"apps.compta.{function_name.lower()}"
            ),
            vat=make_vat("001"),
        )

    return _factory


@pytest.fixture
def bi_maisons_table(db) -> Callable[..., None]:  # pylint: disable=W0613
    """Table B.I heron_bi_maisons (FDW en production) : code_maison -> reference_cosium"""
    with connection.cursor() as cursor:
        cursor.execute(
            "create table if not exists heron_bi_maisons (code_maison text, reference_cosium text)"
        )

    def _insert(code_maison: str, reference_cosium: str) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                "insert into heron_bi_maisons (code_maison, reference_cosium) values (%s, %s)",
                [code_maison, reference_cosium],
            )

    return _insert
