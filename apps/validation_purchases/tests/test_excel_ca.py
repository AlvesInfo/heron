"""Tests des exports 5.3 CA Cosium / Ventes Héron (par cct et par familles)"""

import io
import logging
from decimal import Decimal

import pytest

from apps.core.excel_outputs import generic_list_export
from apps.validation_purchases.excel_outputs import excel_ca_cct, excel_familly_ca_cct
from apps.validation_purchases.tests.helpers_excel_2 import MONTH_M, MONTH_M1
from conftest import patched_attrs

pytestmark = pytest.mark.django_db


@pytest.fixture
def ca_data(make_maison, make_ca_client, make_sale_invoice, make_sale_invoice_detail, make_section):
    """Deux maisons : ventes Héron et CA Cosium sur M et M-1"""
    paris = make_maison("AF0001", intitule_court="PARIS")
    lyon = make_maison("AF0002", intitule_court="LYON")
    opt = make_section("PRO", "OPT", name="Optique")
    aud = make_section("PRO", "AUD", name="Audio")
    make_sale_invoice_detail(
        make_sale_invoice(cct=paris.cct, invoice_amount_without_tax=Decimal(100)),
        axe_pro="OPT",
        net_amount=Decimal(100),
    )
    make_sale_invoice_detail(
        make_sale_invoice(
            cct=paris.cct, invoice_month=MONTH_M1, invoice_amount_without_tax=Decimal(40)
        ),
        axe_pro="AUD",
        net_amount=Decimal(40),
    )
    make_sale_invoice_detail(
        make_sale_invoice(cct=lyon.cct, invoice_amount_without_tax=Decimal(10)),
        axe_pro="OPT",
        net_amount=Decimal(10),
    )
    make_ca_client(maison=paris, axe_pro=opt, ca_ht_eur=Decimal(50))
    make_ca_client(maison=paris, axe_pro=aud, date_ca=MONTH_M1, ca_ht_eur=Decimal(20))
    make_ca_client(maison=lyon, axe_pro=opt, ca_ht_eur=Decimal(5))
    return paris, lyon


@pytest.mark.usefixtures("ca_data")
def test_excel_ca_cct(excel_io):
    file_io = io.BytesIO()

    result = excel_ca_cct.excel_ca_cct(file_io, "ca_cct.xlsx")

    assert "OK" in result
    rows = excel_io(file_io)
    assert rows[0][0] == "5.3 - Contrôle CA Cosium / Ventes Héron"
    data = {row[2]: row for row in rows if row[2] in ("AF0001", "AF0002")}
    # colonnes : enseigne, pays, cct, intitulé, MC, M, PM, M0C, M0, POM, TRIC, TRI, PTM, ANC, AN, PAM
    assert data["AF0001"][3] == "PARIS"
    assert data["AF0001"][4:7] == [50, 100, 2]
    assert data["AF0001"][7:10] == [20, 40, 2]
    assert data["AF0002"][4:7] == [5, 10, 2]
    # entêtes fusionnées des mois M et M-1 en majuscules
    titres = [cell for cell in rows[3] if cell]
    assert titres[0] == MONTH_M.strftime("%B %Y").upper() or titres[0].isupper()


def test_excel_ca_cct_sans_donnees(excel_io):
    file_io = io.BytesIO()

    assert "OK" in excel_ca_cct.excel_ca_cct(file_io, "ca_cct.xlsx")
    assert all(row[2] not in ("AF0001",) for row in excel_io(file_io))


def test_excel_ca_cct_erreur(monkeypatch, caplog):
    def boom(*args, **kwargs):
        raise ValueError("boom")

    with (
        patched_attrs(monkeypatch, generic_list_export, titre_page_writer=boom),
        patched_attrs(monkeypatch, excel_ca_cct, titre_page_writer=boom),
        caplog.at_level(logging.ERROR),
    ):
        result = excel_ca_cct.excel_ca_cct(io.BytesIO(), "ca_cct.xlsx")

    assert result == {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}
    assert "ca_cct.xlsx" in caplog.text


def test_excel_familly_ca_cct(ca_data, excel_io):
    paris, _ = ca_data
    file_io = io.BytesIO()

    result = excel_familly_ca_cct.excel_familly_ca_cct(file_io, "familles.xlsx", paris.cct.cct)

    assert "OK" in result
    rows = excel_io(file_io)
    assert rows[0][0] == "5.3A - Contrôle CA Cosium / Ventes Héron par familles"
    data = {row[4]: row for row in rows if row[2] == "AF0001"}
    assert set(data) == {"Optique", "Audio"}
    assert data["Optique"][5:8] == [50, 100, 2]
    assert data["Audio"][8:11] == [20, 40, 2]
    assert all(row[2] != "AF0002" for row in rows)


def test_excel_familly_ca_cct_erreur(monkeypatch, caplog):
    def boom(*args, **kwargs):
        raise ValueError("boom")

    with (
        patched_attrs(monkeypatch, generic_list_export, titre_page_writer=boom),
        patched_attrs(monkeypatch, excel_familly_ca_cct, titre_page_writer=boom),
        caplog.at_level(logging.ERROR),
    ):
        result = excel_familly_ca_cct.excel_familly_ca_cct(io.BytesIO(), "familles.xlsx", "AF0001")

    assert result == {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}
