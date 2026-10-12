# pylint: disable=E0401,W0621,W0611
"""Tests des exports Excel 3.2 cct/franchiseurs, 5.0 refac par cct et 3.6 période RFA"""
import datetime
import logging
from decimal import Decimal

import pytest

from apps.validation_purchases.excel_outputs import (
    excel_cct_franchiseurs as franchiseurs_module,
    excel_control_rfa_period as rfa_module,
    excel_refac_cct as refac_module,
)
from apps.validation_purchases.tests.helpers_excel import KO, cells, month_ago, run_export

pytestmark = pytest.mark.django_db


# 3.2 CCT / FRANCHISEURS ===========================================================================
def test_cct_franchiseurs(make_edi_row, make_maison, make_purchase_invoice, excel_io):
    franchise = make_maison("AF0001", type_x3=2)
    seconde = make_maison("AF0009", type_x3=2)
    make_maison("AF0002", type_x3=1)
    make_edi_row(maison=franchise, net_amount=Decimal("100"))
    make_edi_row(maison=seconde, net_amount=Decimal("1"))  # second franchiseur : saut de page
    make_edi_row(third_party_num="FOUR002", maison=franchise, net_amount=Decimal("10"))
    make_purchase_invoice(integration_month=month_ago(2), net_amount=Decimal("40"))
    make_purchase_invoice(integration_month=month_ago(12), net_amount=Decimal("12"))

    result, file_io = run_export(franchiseurs_module.excel_cct_franchiseurs, "FRANCHISEURS.xlsx")

    assert "OK" in result
    rows = excel_io(file_io)
    assert rows[0][0] == "3.2 - Contrôle des CCT/franchiseurs (MARK, INFO, etc…)"
    assert cells(rows, "AF0001 - Maison AF0001")
    assert cells(rows, "AF0009 - Maison AF0009")
    assert not cells(rows, "AF0002 - Maison AF0002")
    four = next(row for row in rows if row[0] == "FOUR001 - FOUR001")
    assert four[12] == 100
    assert four[11] == 40
    assert four[1] == 12
    assert four[13] == 140


def test_cct_franchiseurs_erreur(ko_writer, caplog):
    ko_writer(franchiseurs_module)

    with caplog.at_level(logging.ERROR):
        result, _ = run_export(franchiseurs_module.excel_cct_franchiseurs, "FRANCHISEURS.xlsx")

    assert result == KO


# 5.0 REFAC PAR CCT ================================================================================
@pytest.mark.usefixtures('validation_period')
def test_refac_cct(make_edi_row, make_maison, make_purchase_invoice, excel_io):
    initial = datetime.date(2026, 1, 1)
    paris = make_maison("AF0001", type_x3=1)
    make_edi_row(maison=paris, net_amount=Decimal("100"))
    make_purchase_invoice(integration_month=datetime.date(2025, 12, 1), net_amount=Decimal("30"))
    make_purchase_invoice(integration_month=datetime.date(2025, 10, 1), net_amount=Decimal("10"))

    result, file_io = run_export(refac_module.excel_refac_cct, "REFAC.xlsx", {"initial_date": initial})

    assert "OK" in result
    rows = excel_io(file_io)
    assert rows[0][0] == "5.0 - Contrôle Refac M M-1 par CCT"
    assert rows[3][6] == "Octobre\n2025"
    assert rows[3][9] == "Janvier\n2026"
    data = next(row for row in rows if row[2] == "AF0001 - Maison AF0001")
    assert data[0] == "Enseigne ACF" or data[0]
    assert (data[6], data[7], data[8], data[9]) == (10, 0, 30, 100)
    assert data[10] == 70


def test_refac_cct_sans_periode(excel_io):
    result, file_io = run_export(refac_module.excel_refac_cct, "REFAC.xlsx", {"initial_date": month_ago(0)})

    assert "OK" in result
    assert excel_io(file_io)[0][0] == "5.0 - Contrôle Refac M M-1 par CCT"


@pytest.mark.usefixtures('validation_period')
def test_refac_cct_erreur(ko_writer, caplog):
    ko_writer(refac_module)

    with caplog.at_level(logging.ERROR):
        result, _ = run_export(refac_module.excel_refac_cct, "REFAC.xlsx", {"initial_date": datetime.date(2026, 1, 1)})

    assert result == KO


# 3.6 CONTROLE PERIODE RFA =========================================================================
def test_control_rfa_period(make_edi_row, make_section, make_edi_import_control, excel_io):
    control = make_edi_import_control()
    make_edi_row(axe_rfa=make_section("RFA", "RFA1"), uuid_control=control, invoice_number="F1", reference_article="ART-RFA")
    make_edi_row(axe_rfa=make_section("RFA", "RFA1"), uuid_control=control, invoice_number="F2", reference_article="ART-RFA")
    make_edi_row(axe_rfa=make_section("RFA", "NAF"), invoice_number="F3")  # exclu

    rows_db = rfa_module.get_rows(
        __import__("pathlib").Path(f"{__import__('heron.settings.base', fromlist=['APPS_DIR']).APPS_DIR}/validation_purchases/sql_files/sql_control_rfa_period.sql")
    )
    assert len(rows_db) == 1
    assert rows_db[0][4] == "F1, F2"
    assert rows_db[0][6] == "RFA1"

    result, file_io = run_export(rfa_module.control_rfa_period_excel, "RFA.xlsx")

    assert "OK" in result
    rows = excel_io(file_io)
    assert rows[0][0] == "3.6 - Contrôle période RFA"
    assert cells(rows, "F1, F2")
    assert cells(rows, "ART-RFA")
    assert not cells(rows, "F3")


def test_control_rfa_period_erreur(ko_writer, caplog):
    ko_writer(rfa_module)

    with caplog.at_level(logging.ERROR):
        result, _ = run_export(rfa_module.control_rfa_period_excel, "RFA.xlsx")

    assert result == KO
