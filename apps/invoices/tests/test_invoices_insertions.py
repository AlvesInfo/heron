"""Tests de l'insertion des factures d'achat et de vente depuis edi_ediimport (SQL réelles)"""
import datetime
import importlib
import platform
import sys
import types
from decimal import Decimal

import pytest
from django.db import connection

from apps.core.models import SSEProgress
from apps.data_flux.postgres_save import PostgresKeyError, PostgresTypeError
from apps.edi.models import EdiImport
from apps.invoices.bin import invoices_insertions
from apps.invoices.loops.mise_a_jour_loop import process_update
from apps.invoices.models import Invoice, InvoiceCommonDetails, InvoiceDetail, SaleInvoice, SaleInvoiceDetail
from conftest import patched_attrs, raising_once

pytestmark = pytest.mark.django_db
INVOICE_DATE = "2026-01-31"


def run_insertion(dataset):
    """Lance l'insertion complète et renvoie (trace, message)"""
    return invoices_insertions.invoices_insertion(
        dataset.user.uuid_identification, INVOICE_DATE, dataset.progress.job_id
    )


# ÉTAPES UNITAIRES =================================================================================
@pytest.mark.usefixtures('billing_dataset')
def test_set_fix_uuid():
    EdiImport.objects.update(import_uuid_identification=None)

    with connection.cursor() as cursor:
        invoices_insertions.set_fix_uuid(cursor)

    assert not EdiImport.objects.filter(import_uuid_identification__isnull=True).exists()


def test_set_common_details(billing_dataset):
    with connection.cursor() as cursor:
        invoices_insertions.set_fix_uuid(cursor)
        invoices_insertions.set_common_details(cursor)

    rows = list(InvoiceCommonDetails.objects.order_by("id"))
    assert len(rows) == 2
    assert rows[0].cct == billing_dataset.maison.cct
    assert rows[0].unit_weight == "U"
    assert rows[0].uuid_validation == billing_dataset.validation.uuid_identification
    assert rows[0].final is False


def test_set_purchases_invoices(billing_dataset):
    process_update()

    with connection.cursor() as cursor:
        error, _ = invoices_insertions.set_purchases_invoices(cursor, billing_dataset.user, INVOICE_DATE)

    assert error is False
    invoice = Invoice.objects.get()
    assert invoice.invoice_number == "F2026-001"
    assert invoice.invoice_sage_number == "FOUR0012601" + "00001"
    assert invoice.invoice_amount_with_tax == Decimal("180")
    assert invoice.mode_reglement == "VIR"
    assert invoice.code_center == "ACF"
    # échéance : fin de mois (end_month 2) + 1 mois -> 28/02/2026
    assert invoice.date_echeance == datetime.date(2026, 2, 28)
    assert invoice.created_by == billing_dataset.user
    assert invoice.integration_month == datetime.date(2026, 1, 1)


@pytest.mark.parametrize("exception", [PostgresKeyError("clé"), PostgresTypeError("type"), RuntimeError("boom")])
def test_set_purchases_invoices_erreurs(billing_dataset, monkeypatch, exception, caplog):
    def boom(*args, **kwargs):
        raise exception

    with patched_attrs(monkeypatch, invoices_insertions, PostgresDjangoUpsert=boom), caplog.at_level("ERROR", logger="edi"):
        with connection.cursor() as cursor:
            error, _ = invoices_insertions.set_purchases_invoices(cursor, billing_dataset.user, INVOICE_DATE)

    assert error is True
    assert type(exception).__name__ in caplog.text or "Exception Générale" in caplog.text


def test_set_sales_invoices(billing_dataset):
    process_update()

    with connection.cursor() as cursor:
        error, _ = invoices_insertions.set_sales_invoices(cursor, billing_dataset.user, INVOICE_DATE)

    assert error is False
    sale = SaleInvoice.objects.get()
    assert sale.invoice_number == "20260100001"
    assert sale.cct == billing_dataset.maison.cct
    assert sale.invoice_type == "FAC"
    assert sale.invoice_type_name == "Facture"
    assert sale.invoice_amount_without_tax == Decimal("150")
    assert sale.invoice_amount_tax == Decimal("30")
    assert sale.big_category_slug_name == "marchandises"
    assert sale.invoice_date == datetime.date(2026, 1, 31)
    assert sale.centers is not None
    assert sale.signboard is not None
    assert sale.parties is not None


@pytest.mark.parametrize("exception", [PostgresKeyError("clé"), PostgresTypeError("type"), RuntimeError("boom")])
def test_set_sales_invoices_erreurs(billing_dataset, monkeypatch, exception, caplog):
    def boom(*args, **kwargs):
        raise exception

    with patched_attrs(monkeypatch, invoices_insertions, PostgresDjangoUpsert=boom), caplog.at_level("ERROR", logger="edi"):
        with connection.cursor() as cursor:
            error, _ = invoices_insertions.set_sales_invoices(cursor, billing_dataset.user, INVOICE_DATE)

    assert error is True


def test_controls_insertion(make_invoice, make_sale_invoice, make_detail, make_sale_detail):
    with connection.cursor() as cursor:
        assert invoices_insertions.control_purchases_insertion(cursor) is False
        assert invoices_insertions.control_sales_insertion(cursor) is False

    invoice = make_invoice(invoice_amount_without_tax=Decimal("999"))
    make_detail(invoice)
    sale = make_sale_invoice(invoice_amount_tax=Decimal("999"))
    make_sale_detail(sale)

    with connection.cursor() as cursor:
        assert invoices_insertions.control_purchases_insertion(cursor) is True
        assert invoices_insertions.control_sales_insertion(cursor) is True


def test_num_full_sales_invoices(make_sale_invoice, make_counter):
    make_counter("generic", lpad_num=4)
    invoices_insertions.num_full_sales_invoices()  # aucune vente : rien à numéroter

    paris_1 = make_sale_invoice("AF0001")
    paris_2 = make_sale_invoice("AF0001")
    lyon = make_sale_invoice("AF0002")
    final = make_sale_invoice("AF0003", final=True)

    invoices_insertions.num_full_sales_invoices()

    for row in (paris_1, paris_2, lyon, final):
        row.refresh_from_db()
    assert paris_1.global_invoice_file == paris_2.global_invoice_file == "AF0001_0001_full.pdf"
    assert lyon.global_invoice_file == "AF0002_0002_full.pdf"
    assert not final.global_invoice_file


def test_delete_pdf_files(make_sale_invoice, invoices_dirs, settings):
    # delete_pdf_files lit django.conf.settings (et non le module heron.settings)
    settings.SALES_INVOICES_FILES_DIR = invoices_dirs.sales
    existing = invoices_dirs.sales / "AF0001_full.pdf"
    existing.write_bytes(b"%PDF")
    make_sale_invoice("AF0001", global_invoice_file="AF0001_full.pdf")
    make_sale_invoice("AF0002", global_invoice_file="absent.pdf")
    make_sale_invoice("AF0003", global_invoice_file=None)

    with connection.cursor() as cursor:
        invoices_insertions.delete_pdf_files(cursor)

    assert not existing.exists()


def test_reinitialize_nums(make_invoice, make_sale_invoice, invoice_counters):
    from apps.parameters.models import CounterNums

    make_invoice(invoice_sage_number="FOUR00126000012")
    make_sale_invoice(invoice_number="20260100007")

    with connection.cursor() as cursor:
        invoices_insertions.reinitialize_purchase_invoices_nums(cursor)
        invoices_insertions.reinitialize_sales_invoices_nums(cursor)

    assert CounterNums.objects.get(counter=invoice_counters.purchase).num == 13
    assert CounterNums.objects.get(counter=invoice_counters.sales).num == 8


def test_reinitialize_nums_sans_factures_ni_compteurs(make_counter):
    """Sans facture, le compteur repart à 1 ; sans compteur connu, rien ne casse"""
    from apps.parameters.models import CounterNums

    with connection.cursor() as cursor:
        invoices_insertions.reinitialize_purchase_invoices_nums(cursor)
        invoices_insertions.reinitialize_sales_invoices_nums(cursor)

    make_counter("purchase_num", num=9, uuid_identification=invoices_insertions.UUID("ad95c27f-9800-46d4-8e63-55191023f0a4"))

    with connection.cursor() as cursor:
        invoices_insertions.reinitialize_purchase_invoices_nums(cursor)

    assert CounterNums.objects.get(counter__name="purchase_num").num == 1


def test_sanitaze_before(make_invoice, make_detail, make_sale_invoice, make_sale_detail, make_invoice_common_details, invoices_dirs, settings):
    settings.SALES_INVOICES_FILES_DIR = invoices_dirs.sales
    keep = make_invoice(final=True)
    make_detail(keep, final=True)
    make_detail(make_invoice())
    make_sale_detail(make_sale_invoice("AF0001"))
    make_invoice_common_details(final=False)
    make_invoice_common_details("FOUR002", "FAC-9", final=True)

    with connection.cursor() as cursor:
        invoices_insertions.sanitaze_before(cursor)

    assert list(Invoice.objects.all()) == [keep]
    assert InvoiceDetail.objects.count() == 1
    assert SaleInvoice.objects.count() == 0
    assert SaleInvoiceDetail.objects.count() == 0
    assert InvoiceCommonDetails.objects.get().final is True


def test_copy_edi_import(make_edi_import):
    with connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS edi_ediimport_copy")
        invoices_insertions.copy_edi_import(cursor)
        cursor.execute("select to_regclass('edi_ediimport_copy')")
        assert cursor.fetchone()[0] is None

        make_edi_import()
        invoices_insertions.copy_edi_import(cursor)
        cursor.execute("select count(*) from edi_ediimport_copy")
        assert cursor.fetchone()[0] == 1
        cursor.execute("DROP TABLE IF EXISTS edi_ediimport_copy")


class ClosedStringIO(__import__("io").StringIO):
    """StringIO qui se déclare fermé : la fermeture du buffer est alors sautée"""

    @property
    def closed(self):
        return True


class BrokenStringIO(__import__("io").StringIO):
    """StringIO dont l'attribut closed est cassé : la fermeture lève AttributeError (attrapée)"""

    @property
    def closed(self):
        raise AttributeError("closed")


@pytest.mark.parametrize("function", ["set_purchases_invoices", "set_sales_invoices"])
@pytest.mark.parametrize("buffer", [ClosedStringIO, BrokenStringIO])
def test_fermeture_du_buffer(billing_dataset, monkeypatch, function, buffer):
    """Les branches de fermeture du buffer csv (déjà fermé, attribut cassé) ne font pas échouer"""
    process_update()

    with patched_attrs(monkeypatch, invoices_insertions.io, StringIO=buffer):
        with connection.cursor() as cursor:
            error, _ = getattr(invoices_insertions, function)(cursor, billing_dataset.user, INVOICE_DATE)

    assert error is False


# PROCESSUS COMPLET ================================================================================
@pytest.mark.usefixtures('keep_connection', 'sync_controls')
def test_invoices_insertion_complete(billing_dataset, monkeypatch):
    """Pré-contrôle sans manquant, insertion complète achats + ventes"""
    with patched_attrs(monkeypatch, invoices_insertions, control_alls_missings=lambda: {}):
        trace, message = run_insertion(billing_dataset)

    assert message == ""
    assert trace.trace_name.startswith("Insertion de la facturation")
    billing_dataset.validation.refresh_from_db()
    assert billing_dataset.validation.billing_date == datetime.date(2026, 1, 31)

    invoice = Invoice.objects.get()
    assert InvoiceDetail.objects.filter(uuid_invoice=invoice).count() == 2
    assert invoice.invoice_type_name == "Facture"
    assert invoice.regime_tva_tiers == "FRA"
    assert set(InvoiceDetail.objects.values_list("collectif", flat=True)) == {"607"}

    sale = SaleInvoice.objects.get()
    details = list(SaleInvoiceDetail.objects.filter(uuid_invoice=sale).order_by("net_amount"))
    assert [row.net_amount for row in details] == [Decimal("50"), Decimal("100")]
    assert details[0].account == "707000"
    assert details[0].grouping_goods == "MONTURES"
    assert sale.collectif == "707"
    assert sale.regime_tva_maison == "FRA"
    assert sale.global_invoice_file == "AF0001_0001_full.pdf"
    assert InvoiceCommonDetails.objects.count() == 2

    progress = SSEProgress.objects.get(job_id=billing_dataset.progress.job_id)
    assert progress.status == "completed"
    assert progress.processed_items >= 12


@pytest.mark.usefixtures('keep_connection', 'sync_controls')
def test_invoices_insertion_erreur_controle_achats(billing_dataset, monkeypatch, caplog):
    """Contrôle des achats en échec ; le pré-contrôle renvoie aussi des manquants (branche non bloquante)"""
    with patched_attrs(
        monkeypatch, invoices_insertions,
        control_purchases_insertion=lambda cursor: True,
        control_alls_missings=lambda: {"tiers": ("Il manque des tiers X3", "")},
    ), caplog.at_level("ERROR", logger="edi"):
        _, message = run_insertion(billing_dataset)

    assert "factures d'achat" in message
    assert SSEProgress.objects.get(job_id=billing_dataset.progress.job_id).status == "failed"
    assert "factures d'achat" in caplog.text


@pytest.mark.usefixtures('keep_connection', 'sync_controls')
def test_invoices_insertion_erreur_entetes_achats(billing_dataset, monkeypatch):
    with patched_attrs(monkeypatch, invoices_insertions, set_purchases_invoices=lambda c, u, d: (True, "ko")):
        run_insertion(billing_dataset)

    assert SSEProgress.objects.get(job_id=billing_dataset.progress.job_id).status == "failed"
    assert Invoice.objects.count() == 0


@pytest.mark.usefixtures('keep_connection', 'sync_controls')
def test_invoices_insertion_erreur_entetes_ventes(billing_dataset, monkeypatch):
    with patched_attrs(monkeypatch, invoices_insertions, set_sales_invoices=lambda c, u, d: (True, "ko")):
        run_insertion(billing_dataset)

    assert SSEProgress.objects.get(job_id=billing_dataset.progress.job_id).status == "failed"


@pytest.mark.usefixtures('keep_connection', 'sync_controls')
def test_invoices_insertion_erreur_controle_ventes(billing_dataset, monkeypatch):
    with patched_attrs(monkeypatch, invoices_insertions, control_sales_insertion=lambda cursor: True):
        _, message = run_insertion(billing_dataset)

    assert "factures de vente" in message
    assert SSEProgress.objects.get(job_id=billing_dataset.progress.job_id).status == "failed"


@pytest.mark.parametrize("exception", [PostgresKeyError("clé"), PostgresTypeError("type")])
@pytest.mark.usefixtures('keep_connection', 'sync_controls')
def test_invoices_insertion_erreurs_postgres(billing_dataset, monkeypatch, exception, caplog):
    with raising_once(exception) as boom, patched_attrs(monkeypatch, invoices_insertions, set_fix_uuid=boom), caplog.at_level("ERROR", logger="edi"):
        run_insertion(billing_dataset)

    assert type(exception).__name__ in caplog.text
    assert SSEProgress.objects.get(job_id=billing_dataset.progress.job_id).status == "failed"


@pytest.mark.parametrize(("node", "expected"), [("MSI", r"C:\SitesWeb\heron"), ("serveur", "/home/paulo/heron")])
def test_base_dir_selon_la_machine(monkeypatch, node, expected):
    monkeypatch.setattr(sys, "path", list(sys.path))

    try:
        with patched_attrs(monkeypatch, platform, uname=lambda: types.SimpleNamespace(node=node)):
            assert expected == importlib.reload(invoices_insertions).BASE_DIR
    finally:
        importlib.reload(invoices_insertions)
