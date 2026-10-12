# pylint: disable=E0401,W0621,W0611
"""Tests des exports Excel par fournisseur (factures, détails, pièce, familles, M vs M-1)"""

import datetime
import logging
from decimal import Decimal

import pytest

from apps.validation_purchases.excel_outputs import (
    excel_balance_suppliers_purchases as balance_module,
    excel_supplier_details_invoices_familly as familly_module,
    excel_supplier_invoices_details as details_module,
    excel_supplier_invoices_list as list_module,
    excel_supplier_invoices_number as number_module,
)
from apps.validation_purchases.tests.helpers_excel import KO, cells, month_ago, run_export

pytestmark = pytest.mark.django_db

ATTR = {
    "third_party_num": "FOUR001",
    "supplier": "FOURNISSEUR 1",
    "invoice_month": "2026-01-01",
    "flow_name": "Widex",
}


@pytest.fixture
def supplier_invoices(make_edi_row, make_maison):
    """Trois factures : mono-magasin, multi-magasins complet, multi-magasins partiel, plus un avoir"""
    paris, lyon = (
        make_maison("AF0001", code_maison="AF0001"),
        make_maison("AF0002", code_maison="AF0002"),
    )
    make_edi_row(maison=paris, invoice_number="F1")
    make_edi_row(maison=paris, invoice_number="F2", is_multi_store=True)
    make_edi_row(maison=lyon, invoice_number="F2", is_multi_store=True, net_amount=Decimal(0))
    make_edi_row(maison=paris, invoice_number="F3", is_multi_store=True)
    make_edi_row(cct=None, invoice_number="F3", is_multi_store=True)
    make_edi_row(cct=None, invoice_number="F4")
    make_edi_row(maison=paris, invoice_number="A1", invoice_type="381", net_amount=Decimal(-100))
    return paris


@pytest.mark.usefixtures("supplier_invoices")
def test_supplier_purchases(excel_io):
    result, file_io = run_export(list_module.excel_supplier_purchases, "FOUR001.xlsx", ATTR)

    assert "OK" in result
    rows = excel_io(file_io)
    assert rows[0][0] == "Factures : FOUR001 - FOURNISSEUR 1 - pour janvier 2026"
    by_number = {row[6]: row for row in rows if row[0] == "FOUR001"}
    assert set(by_number) == {"F1", "F2", "F3", "F4", "A1"}
    assert by_number["F1"][2] == "AF0001"
    assert by_number["F1"][5] == "FAF"
    assert not by_number["F2"][2]
    assert by_number["F2"][4] == "Multi Magasins !"
    assert by_number["F3"][4] == "Multi Magasins !"
    assert not by_number["F4"][2]
    assert by_number["A1"][5] == "AVO"


def test_supplier_purchases_erreur(ko_writer, caplog):
    ko_writer(list_module)

    with caplog.at_level(logging.ERROR):
        result, _ = run_export(list_module.excel_supplier_purchases, "FOUR001.xlsx", ATTR)

    assert result == KO


@pytest.mark.usefixtures("supplier_invoices")
def test_invoice_details(excel_io):
    result, file_io = run_export(details_module.excel_invoice_details, "DETAILS.xlsx", ATTR)

    assert "OK" in result
    rows = excel_io(file_io)
    assert rows[0][0] == "FOUR001 - FOURNISSEUR 1 : Janvier 2026"
    data = [row for row in rows if row[0] == "FOUR001"]
    assert len(data) == 7
    assert data[0][2] == "Facture"
    assert data[0][9] == "AF0001"
    assert any(row[2] == "Avoir" for row in data)
    # remise = 1 - net / brut = 1 - 100/120
    assert round(data[0][18], 2) == 0.17


def test_invoice_details_erreur(ko_writer, caplog):
    ko_writer(details_module)

    with caplog.at_level(logging.ERROR):
        result, _ = run_export(details_module.excel_invoice_details, "DETAILS.xlsx", ATTR)

    assert result == KO


@pytest.mark.usefixtures("supplier_invoices")
def test_invoice_number(excel_io):
    attr = {"third_party_num": "FOUR001", "supplier": "FOURNISSEUR 1", "invoice_number": "F2"}

    result, file_io = run_export(number_module.excel_invoice_number, "F2.xlsx", attr)

    assert "OK" in result
    rows = excel_io(file_io)
    assert rows[0][0] == "FOUR001 - FOURNISSEUR 1 : Pièce N° F2"
    data = [row for row in rows if row[0] == "FOUR001"]
    assert len(data) == 2
    assert {row[9] for row in data} == {"AF0001", "AF0002"}


def test_invoice_number_erreur(ko_writer, caplog):
    ko_writer(number_module)

    with caplog.at_level(logging.ERROR):
        result, _ = run_export(
            number_module.excel_invoice_number,
            "F2.xlsx",
            {"third_party_num": "X", "invoice_number": "1"},
        )

    assert result == KO


@pytest.mark.usefixtures("supplier_invoices")
def test_supplier_details_invoice(excel_io):
    result, file_io = run_export(
        familly_module.excel_supplier_details_invoice,
        "FAMILLES.xlsx",
        {"third_party_num": "FOUR001"},
    )

    assert "OK" in result
    rows = excel_io(file_io)
    assert rows[0][0] == "ETAPE 3.1.A: CONTROLES DE FAMILLES : FOUR001 - FOURNISSEUR 1"
    assert cells(rows, "OPT")
    assert cells(rows, "Marchandises")


def test_supplier_details_invoice_sans_lignes(excel_io):
    """Sans facture, le nom du fournisseur du titre est vide (IndexError attrapé)"""
    result, file_io = run_export(
        familly_module.excel_supplier_details_invoice,
        "FAMILLES.xlsx",
        {"third_party_num": "INCONNU"},
    )

    assert "OK" in result
    assert excel_io(file_io)[0][0] == "ETAPE 3.1.A: CONTROLES DE FAMILLES : INCONNU - "


def test_supplier_details_invoice_erreur(ko_writer, caplog):
    ko_writer(familly_module)

    with caplog.at_level(logging.ERROR):
        result, _ = run_export(
            familly_module.excel_supplier_details_invoice, "FAMILLES.xlsx", {"third_party_num": "X"}
        )

    assert result == KO


# 5.1 FOURNISSEURS M vs M-1 ========================================================================
@pytest.mark.usefixtures("validation_period")
def test_balance_suppliers_purchases(make_edi_row, make_purchase_invoice, excel_io):
    initial = datetime.date(2026, 1, 1)
    make_edi_row(net_amount=Decimal(100))
    make_purchase_invoice(integration_month=initial, net_amount=Decimal(40))
    make_purchase_invoice(integration_month=datetime.date(2025, 12, 1), net_amount=Decimal(30))
    make_purchase_invoice(integration_month=datetime.date(2025, 10, 1), net_amount=Decimal(10))
    make_purchase_invoice(
        integration_month=datetime.date(2025, 6, 1), net_amount=Decimal(999)
    )  # hors fenêtre

    result, file_io = run_export(
        balance_module.excel_balance_suppliers_purchases,
        "FOURNISSEURS.xlsx",
        {"initial_date": initial},
    )

    assert "OK" in result
    rows = excel_io(file_io)
    assert rows[0][0] == "5.1 Fournisseurs M vs M-1"
    assert rows[3][2] == "Octobre\n2025"
    assert rows[3][5] == "Janvier\n2026"
    data = next(row for row in rows if row[0] == "FOUR001")
    assert (data[2], data[3], data[4], data[5]) == (10, 0, 30, 140)
    assert data[6] == 110


def test_balance_suppliers_sans_periode_de_validation(excel_io):
    """Sans EdiValidation ouverte, les en-têtes partent du mois courant (plus d'AttributeError)"""
    result, file_io = run_export(
        balance_module.excel_balance_suppliers_purchases,
        "FOURNISSEURS.xlsx",
        {"initial_date": month_ago(0)},
    )

    assert "OK" in result
    assert excel_io(file_io)[0][0] == "5.1 Fournisseurs M vs M-1"


@pytest.mark.usefixtures("validation_period")
def test_balance_suppliers_erreur(ko_writer, caplog):
    ko_writer(balance_module)

    with caplog.at_level(logging.ERROR):
        result, _ = run_export(
            balance_module.excel_balance_suppliers_purchases,
            "F.xlsx",
            {"initial_date": datetime.date(2026, 1, 1)},
        )

    assert result == KO
