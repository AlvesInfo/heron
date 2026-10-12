"""Tests des exports 5.A / 5.B : fournisseurs M vs M-1 d'une maison, et détail d'un fournisseur"""

import io
import logging
from decimal import Decimal

import pytest

from apps.core.excel_outputs import generic_list_export
from apps.validation_purchases.excel_outputs import (
    excel_suppliers_m_vs_m1,
    excel_third_suppliers_m_vs_m1,
)
from apps.validation_purchases.tests.helpers_excel_2 import MONTH_M, MONTH_M1
from conftest import patched_attrs

pytestmark = pytest.mark.django_db


@pytest.fixture
def suppliers_data(make_maison, make_edi_import, make_purchase_invoice_2, make_society):
    """Maison AF0001 : achats edi du mois en cours (M_00) et factures finalisées M-1 / M-2"""
    maison = make_maison("AF0001", intitule="Maison Paris")
    make_society("FOUR001", is_client=False, name="Fournisseur Un")
    make_society("FOUR002", is_client=False, name="Fournisseur Deux")
    make_edi_import(
        "FOUR001",
        "A1",
        cct_uuid_identification=maison,
        purchase_invoice=True,
        net_amount=Decimal(100),
        invoice_number="E1",
        invoice_date=MONTH_M,
    )
    make_edi_import(
        "FOUR001",
        "A2",
        cct_uuid_identification=maison,
        purchase_invoice=True,
        net_amount=Decimal(0),
        invoice_number="E0",
        invoice_date=MONTH_M,
    )
    make_edi_import(
        "FOUR002",
        "B1",
        cct_uuid_identification=maison,
        purchase_invoice=True,
        net_amount=Decimal(30),
        invoice_number="E2",
        invoice_date=MONTH_M,
    )
    make_purchase_invoice_2(
        maison.cct, "FOUR001", integration_month=MONTH_M1, net_amount=Decimal(60)
    )
    make_purchase_invoice_2(
        maison.cct, "FOUR001", integration_month=MONTH_M1, final=False, net_amount=Decimal(999)
    )
    return maison


def test_excel_suppliers_m_vs_m1(suppliers_data, excel_io):
    file_io = io.BytesIO()

    result = excel_suppliers_m_vs_m1.excel_suppliers_m_vs_m1(
        file_io, "m_m1.xlsx", suppliers_data.cct.cct
    )

    assert "OK" in result
    rows = excel_io(file_io)
    assert rows[0][0] == "5.A - Contrôle Fournisseurs M vs M-1"
    # bloc client : cct - intitulé, enseigne, pays, ouverture, fermeture
    assert rows[4][0] == "AF0001 - Maison Paris"
    assert rows[4][2] == "France" or rows[4][2] == "Pays FR"
    # lignes fournisseurs : tiers, M-3, M-2, M-1, M, variation, commentaire
    data = {row[0]: row for row in rows[7:] if row[0]}
    assert data["FOUR001 - Fournisseur Un"][1:6] == [0, 0, 60, 100, 40]
    assert data["FOUR002 - Fournisseur Deux"][1:6] == [0, 0, 0, 30, 30]
    # entêtes des mois en deux lignes
    assert "\n" in rows[6][1]


def test_excel_suppliers_m_vs_m1_sans_donnees(excel_io):
    file_io = io.BytesIO()

    assert "OK" in excel_suppliers_m_vs_m1.excel_suppliers_m_vs_m1(file_io, "m_m1.xlsx", "ZZ9999")
    rows = excel_io(file_io)
    assert all(cell is None for cell in rows[4][:5])


def test_excel_suppliers_m_vs_m1_erreur(monkeypatch, caplog):
    def boom(*args, **kwargs):
        raise ValueError("boom")

    with (
        patched_attrs(monkeypatch, generic_list_export, titre_page_writer=boom),
        patched_attrs(monkeypatch, excel_suppliers_m_vs_m1, titre_page_writer=boom),
        caplog.at_level(logging.ERROR),
    ):
        result = excel_suppliers_m_vs_m1.excel_suppliers_m_vs_m1(
            io.BytesIO(), "m_m1.xlsx", "AF0001"
        )

    assert result == {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}
    assert "m_m1.xlsx" in caplog.text


def test_excel_third_suppliers_m_vs_m1(suppliers_data, excel_io):
    file_io = io.BytesIO()

    result = excel_third_suppliers_m_vs_m1.excel_third_suppliers_m_vs_m1(
        file_io, "detail.xlsx", suppliers_data.cct.cct, "FOUR001"
    )

    assert "OK" in result
    rows = excel_io(file_io)
    assert rows[0][0] == "5.B - Contrôle Details Fournisseurs M vs M-1"
    data = [row for row in rows if row[0] == "AF0001"]
    assert len(data) == 1
    assert data[0][2] == "FOUR001 - Fournisseur Un"
    assert data[0][3] == "E1"
    assert data[0][7] == 100


def test_excel_third_suppliers_m_vs_m1_erreur(monkeypatch, caplog):
    def boom(*args, **kwargs):
        raise ValueError("boom")

    with (
        patched_attrs(monkeypatch, generic_list_export, titre_page_writer=boom),
        patched_attrs(monkeypatch, excel_third_suppliers_m_vs_m1, titre_page_writer=boom),
        caplog.at_level(logging.ERROR),
    ):
        result = excel_third_suppliers_m_vs_m1.excel_third_suppliers_m_vs_m1(
            io.BytesIO(), "d.xlsx", "AF0001", "FOUR001"
        )

    assert result == {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}
