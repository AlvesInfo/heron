"""Tests de l'export des RFA mensuelles (détail, résumé par clients, résumé par enseignes)"""

import io
import logging
from decimal import Decimal

import openpyxl
import pytest

from apps.core.excel_outputs import generic_list_export
from apps.validation_purchases.excel_outputs import output_excel_rfa_mensuelles as rfa
from apps.validation_purchases.excel_outputs.columns_excel import (
    columns_rfa_cct,
    columns_rfa_signboard,
)
from conftest import patched_attrs

pytestmark = pytest.mark.django_db


def read_sheets(file_io):
    file_io.seek(0)
    book = openpyxl.load_workbook(file_io)
    return {
        sheet.title: [[cell.value for cell in row] for row in sheet.iter_rows()]
        for sheet in book.worksheets
    }


@pytest.fixture
def rfa_data(make_maison, make_signboard, make_edi_import, make_supplier_rate, make_society):
    """Deux enseignes, trois maisons, deux fournisseurs à taux RFA et un sans taux"""
    make_supplier_rate("FOUR001")
    make_supplier_rate("FOUR002")
    make_society("FOUR003", is_client=False)
    paris = make_maison("AF0001", intitule="Paris")
    lyon = make_maison("AF0002", intitule="Lyon")
    nice = make_maison("AF0003", intitule="Nice", sign_board=make_signboard("GAF"))
    rows = [
        (paris, "FOUR001", "ACF", Decimal(100)),
        (paris, "FOUR002", "ACF", Decimal(20)),
        (lyon, "FOUR001", "ACF", Decimal(10)),
        (nice, "FOUR003", "GAF", Decimal(5)),
    ]
    for maison, supplier, signboard, amount in rows:
        make_edi_import(
            supplier,
            f"ART-{supplier}",
            flow_name="rfa_flow",
            cct_uuid_identification=maison,
            code_signboard=signboard,
            net_amount=amount,
            invoice_number=f"F-{maison.cct.cct}-{supplier}",
        )
    make_edi_import(
        "FOUR001", "HORS", flow_name="Widex", net_amount=Decimal(999), invoice_number="HORS"
    )


def test_get_amounts_sql(make_supplier_rate):
    make_supplier_rate("FOUR001")
    make_supplier_rate("FOUR002")

    nb_sums, sum_sql, amount_sql, columns = rfa.get_amounts_sql()

    assert nb_sums == 3
    assert [column["entete"] for column in columns] == ["FOUR001", "FOUR002", "Total HT"]
    assert 'sum("FOUR001") as "FOUR001"' in sum_sql
    assert '"ee"."third_party_num" = \'FOUR002\'' in amount_sql


def test_get_amounts_sql_sans_fournisseur():
    nb_sums, sum_sql, amount_sql, columns = rfa.get_amounts_sql()

    assert (nb_sums, sum_sql, amount_sql) == (1, "", "")
    assert [column["entete"] for column in columns] == ["Total HT"]


@pytest.mark.usefixtures("rfa_data")
def test_get_rows_functions():
    nb_sums, columns, rows = rfa.get_rows()
    assert nb_sums == 14
    assert len(rows) == 4
    assert len(columns) == 34

    nb_sums, columns, rows = rfa.get_rows_resume_cct()
    assert nb_sums == 3
    assert len(columns) == len(columns_rfa_cct) + 3
    by_cct = {row[1]: row for row in rows}
    assert by_cct["AF0001"][3:] == (Decimal(100), Decimal(20), Decimal(120))
    assert by_cct["AF0003"][3:] == (Decimal(0), Decimal(0), Decimal(5))

    nb_sums, columns, rows = rfa.get_rows_resume_signboard()
    assert len(columns) == len(columns_rfa_signboard) + 3
    assert {row[0]: row[1:] for row in rows} == {
        "ACF": (Decimal(110), Decimal(20), Decimal(130)),
        "GAF": (Decimal(0), Decimal(0), Decimal(5)),
    }


@pytest.mark.usefixtures("rfa_data")
def test_excel_rfa_mensuelles():
    file_io = io.BytesIO()

    result = rfa.excel_rfa_mensuelles(file_io, "rfa.xlsx")

    assert "OK" in result
    sheets = read_sheets(file_io)
    assert list(sheets) == ["DETAILS RFA", "PAR CLIENTS", "PAR ENSEIGNES"]
    details = sheets["DETAILS RFA"]
    assert details[0][0] == "DETAILS RFA"
    total = next(row for row in details if "TOTAL" in row)
    # colonne 20 (j=1) somme, colonnes 21-22 vides, 23-24 (j=4, 5) sommes
    assert total[19] == "TOTAL"
    assert str(total[20]).startswith("=SUM(")
    assert total[21] is None
    assert str(total[23]).startswith("=SUM(")
    assert sum(1 for row in details if row[1] == "ACF") == 3
    assert sum(1 for row in details if row[1] == "GAF") == 1
    clients = sheets["PAR CLIENTS"]
    assert [row[1] for row in clients if row[1] in ("AF0001", "AF0002", "AF0003")] == [
        "AF0001",
        "AF0002",
        "AF0003",
    ]
    total_clients = next(row for row in clients if "TOTAL" in row)
    assert total_clients[2] == "TOTAL"
    assert all(str(cell).startswith("=SUM(") for cell in total_clients[3:6])
    enseignes = sheets["PAR ENSEIGNES"]
    assert [row[0] for row in enseignes if row[0] in ("ACF", "GAF")] == ["ACF", "GAF"]
    assert enseignes[3][1:4] == ["FOUR001", "FOUR002", "Total HT"]


def test_excel_rfa_mensuelles_sans_lignes():
    file_io = io.BytesIO()

    assert "OK" in rfa.excel_rfa_mensuelles(file_io, "rfa.xlsx")
    sheets = read_sheets(file_io)
    assert next(row for row in sheets["PAR ENSEIGNES"] if "TOTAL" in row)[0] == "TOTAL"


def test_excel_rfa_mensuelles_erreur(monkeypatch, caplog):
    def boom(*args, **kwargs):
        raise ValueError("boom")

    with (
        patched_attrs(monkeypatch, generic_list_export, titre_page_writer=boom),
        patched_attrs(monkeypatch, rfa, titre_page_writer=boom),
        caplog.at_level(logging.ERROR),
    ):
        result = rfa.excel_rfa_mensuelles(io.BytesIO(), "rfa.xlsx")

    assert result == {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}
    assert "rfa.xlsx" in caplog.text
