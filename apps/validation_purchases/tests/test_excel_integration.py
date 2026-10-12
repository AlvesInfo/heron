# pylint: disable=E0401,W0621,W0611
"""Tests des exports Excel de l'étape 2 (intégrations, familles, sans cct, transferts Cosium)"""
import logging
from decimal import Decimal
from pathlib import Path

import pytest

from apps.validation_purchases.excel_outputs import (
    excel_integration_invoices_familly as familly_module,
    excel_integration_invoices_list as integration_module,
    excel_integration_invoices_without_cct as without_cct_module,
    excel_transfer_invoices_list as transfer_module,
)
from apps.validation_purchases.tests.helpers_excel import KO, cells, month_ago, run_export
from heron.settings.base import APPS_DIR

pytestmark = pytest.mark.django_db


# 2.1 RELEVES VS FACTURES INTEGREES ================================================================
def test_integration_purchases_avec_controle(make_edi_row, make_edi_import_control, excel_io):
    control = make_edi_import_control(statement_without_tax=Decimal("90"), statement_with_tax=Decimal("108"), comment="relevé")
    make_edi_row(uuid_control=control, invoice_number="F1")
    make_edi_row(uuid_control=control, invoice_number="F2", net_amount=Decimal("80"))  # erreur net != HT
    make_edi_row(third_party_num="FOUR002", supplier=None, cct=None, invoice_number="F3")

    result, file_io = run_export(integration_module.excel_integration_purchases, "RELEVES_VS_FACTURES_INTEGREES_x.xlsx")

    assert "OK" in result
    rows = excel_io(file_io)
    assert rows[0][0] == "RELEVES VS FACTURES"
    data = [row for row in rows if row[0] in ("FOUR001", "FOUR002")]
    assert len(data) == 2
    assert data[0][2] == "FOURNISSEUR 1"
    assert data[0][5] == 2
    assert data[0][8] == 90  # relevé HT
    assert data[1][2] == "INCONNU"


def test_integration_purchases_get_rows_ignore_les_non_valides(make_edi_row):
    make_edi_row(valid=False)
    make_edi_row(delete=True)

    rows = integration_module.get_rows(Path(f"{APPS_DIR}/validation_purchases/sql_files/sql_integration_purchases.sql"))

    assert rows == []


def test_integration_purchases_erreur(ko_writer, caplog):
    ko_writer(integration_module)

    with caplog.at_level(logging.ERROR):
        result, _ = run_export(integration_module.excel_integration_purchases, "RELEVES_x.xlsx")

    assert result == KO
    assert "RELEVES_x.xlsx" in caplog.text


# 3.1 FAMILLES =====================================================================================
def test_integration_invoices_familly(make_edi_row, make_purchase_invoice, excel_io):
    make_edi_row(net_amount=Decimal("100"))
    make_purchase_invoice(integration_month=month_ago(1), net_amount=Decimal("40"))
    make_purchase_invoice(integration_month=month_ago(2), net_amount=Decimal("30"))
    make_purchase_invoice(integration_month=month_ago(3), net_amount=Decimal("20"))
    make_purchase_invoice(integration_month=month_ago(1), net_amount=Decimal("5"), axe_pro="AUD")

    result, file_io = run_export(familly_module.excel_integration_invoices_familly, "CONTROLE_FAMILLES_2026_1_1.xlsx")

    assert "OK" in result
    rows = excel_io(file_io)
    assert rows[0][0] == "CONTROLE FAMILLES"
    headers = rows[3]
    assert headers[3].startswith("Mois-2")
    assert headers[5].startswith("Mois M")
    opt = next(row for row in rows if row[0] == "FOUR001" and row[2] == "OPT")
    assert (opt[3], opt[4], opt[5]) == (20, 30, 140)  # M-2, M-1, M (edi 100 + facture 40)
    assert opt[6] == 110  # variation M - M-1
    assert any(row[2] == "AUD" for row in rows if row[0] == "FOUR001")


def test_integration_invoices_familly_erreur(ko_writer, caplog):
    ko_writer(familly_module)

    with caplog.at_level(logging.ERROR):
        result, _ = run_export(familly_module.excel_integration_invoices_familly, "FAMILLES_x_y_z.xlsx")

    assert result == KO


# SANS CCT =========================================================================================
def test_integration_without_cct(make_edi_row, excel_io):
    make_edi_row(cct=None, invoice_number="SANS")
    make_edi_row(cct=None, invoice_number="DEL", delete=True)
    make_edi_row(invoice_number="AVEC")

    rows_db = without_cct_module.get_rows()
    assert [row[5] for row in rows_db] == ["SANS"]

    result, file_io = run_export(without_cct_module.excel_integration_without_cct, "FACTURES_SANS_CCT_2026_1_1.xlsx")

    assert "OK" in result
    rows = excel_io(file_io)
    assert rows[0][0] == "FACTURES SANS CCT"
    assert cells(rows, "SANS")
    assert not cells(rows, "AVEC")


def test_integration_without_cct_erreur(ko_writer, caplog):
    ko_writer(without_cct_module)

    with caplog.at_level(logging.ERROR):
        result, _ = run_export(without_cct_module.excel_integration_without_cct, "SANS_CCT_x_y_z.xlsx")

    assert result == KO


# TRANSFERTS COSIUM ================================================================================
def test_transfers_cosium(make_edi_row, make_maison, bi_maisons_table, excel_io):
    maison = make_maison("AF0007", code_maison="AF0007")
    bi_maisons_table("AF0007", "REF007")
    make_edi_row(third_party_num="ZTRANSFERT", supplier="TRANSFERTS", maison=maison, invoice_number="TS-1", flow_name="Transfert")
    make_edi_row(third_party_num="ZTRANSFERT", supplier="TRANSFERTS", maison=maison, invoice_number="TS-1", flow_name="Transfert", net_amount=Decimal("50"))
    make_edi_row(third_party_num="ZTRANSFERT", supplier="TRANSFERTS", maison=maison, invoice_number="TS-2", invoice_type="381", flow_name="Transfert")
    attr_dict = {"third_party_num": "ZTRANSFERT", "supplier": "TRANSFERTS", "invoice_month": "2026-01-01"}

    rows_db = transfer_module.get_rows(attr_dict)
    assert {(row[6], row[5], row[8]) for row in rows_db} == {("TS-1", "FAF", Decimal("150")), ("TS-2", "AVO", Decimal("100"))}
    assert rows_db[0][3] == "REF007"

    result, file_io = run_export(transfer_module.excel_transfers_cosium, "TRANSFERTS.xlsx", attr_dict)

    assert "OK" in result
    rows = excel_io(file_io)
    assert rows[0][0] == "Factures : ZTRANSFERT - TRANSFERTS - pour janvier 2026"
    assert cells(rows, "TS-1")
    assert cells(rows, "AVO")


@pytest.mark.usefixtures('bi_maisons_table')
def test_transfers_cosium_erreur(ko_writer, caplog):
    ko_writer(transfer_module)
    attr_dict = {"third_party_num": "Z", "supplier": "T", "invoice_month": "2026-01-01"}

    with caplog.at_level(logging.ERROR):
        result, _ = run_export(transfer_module.excel_transfers_cosium, "TRANSFERTS.xlsx", attr_dict)

    assert result == KO
