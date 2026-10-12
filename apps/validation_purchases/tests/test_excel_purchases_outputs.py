"""Tests des exports achats Héron non finalisés et achats import edi"""

import io
import logging
from decimal import Decimal

import pytest

from apps.core.excel_outputs import generic_list_export
from apps.validation_purchases.excel_outputs import (
    columns_excel,
    output_excel_purchases_edi_import as edi_out,
    output_excel_purchases_not_final_optimized as optimized,
)
from conftest import patched_attrs

pytestmark = pytest.mark.django_db


@pytest.fixture
def not_final_data(make_maison, make_purchase_invoice_2, make_society):
    make_society("FOUR001", is_client=False, name="Fournisseur Un")
    maison = make_maison("AF0001")
    make_purchase_invoice_2(maison.cct, "FOUR001", final=False, net_amount=Decimal(80))
    make_purchase_invoice_2(maison.cct, "FOUR001", final=True, net_amount=Decimal(999))
    return maison


def test_columns_excel_listes():
    assert len(columns_excel.columns_purchases_heron) == 36
    assert len(columns_excel.columns_purchases_edi) == 34
    assert len(columns_excel.columns_rfa_mensuelles) == 34
    assert [c["entete"] for c in columns_excel.columns_rfa_signboard] == ["Enseigne"]


@pytest.mark.usefixtures("not_final_data")
def test_purchases_not_final(excel_io):
    file_io = io.BytesIO()

    result = optimized.excel_heron_purchases_not_final(file_io, "achats.xlsx")

    assert "OK" in result
    rows = excel_io(file_io)
    assert rows[0][0] == "ACHATS HERON A FINALISER"
    data = [row for row in rows[4:] if row[2] == "FOUR001"]
    assert len(data) == 1
    assert data[0][3] == "Fournisseur Un"
    assert data[0][9] == "AF0001"
    assert data[0][21] == 80


def test_purchases_not_final_sans_lignes(excel_io):
    file_io = io.BytesIO()

    assert "OK" in optimized.excel_heron_purchases_not_final(file_io, "a.xlsx")
    assert len(excel_io(file_io)) == 4


@pytest.mark.usefixtures("not_final_data")
def test_purchases_not_final_fetch_rows_par_lots():
    """Les lignes sont lues par paquets de 1000 jusqu'à épuisement"""
    rows = list(optimized.fetch_rows())

    assert len(rows) == 1


def test_purchases_not_final_erreur(monkeypatch, caplog):
    def boom(*args, **kwargs):
        raise ValueError("boom")

    with (
        patched_attrs(monkeypatch, generic_list_export, titre_page_writer=boom),
        caplog.at_level(logging.ERROR),
    ):
        assert optimized.excel_heron_purchases_not_final(io.BytesIO(), "o.xlsx") == {
            "KO": "ERREUR DANS LA GENERATION DU FICHIER"
        }

    assert "o.xlsx" in caplog.text


@pytest.fixture
def edi_data(
    make_maison, make_edi_import, make_section, make_big_category, make_sub_category, make_society
):
    make_society("FOUR001", is_client=False, name="Fournisseur Un")
    maison = make_maison("AF0001")
    big = make_big_category("Marchandises")
    return make_edi_import(
        "FOUR001",
        "ART-1",
        cct_uuid_identification=maison,
        invoice_number="E1",
        invoice_type="381",
        axe_bu=make_section("BU", "CAHA"),
        axe_pro=make_section("PRO", "OPT"),
        axe_prj=make_section("PRJ", "NAF"),
        axe_pys=make_section("PYS", "FR"),
        axe_rfa=make_section("RFA", "NAF"),
        big_category=big,
        sub_category=make_sub_category("Montures", big),
        code_center="ACF",
        code_signboard="ACF",
        net_amount=Decimal(-10),
    )


@pytest.mark.usefixtures("edi_data")
def test_purchases_edi_import_excel(excel_io):
    file_io = io.BytesIO()

    result = edi_out.excel_heron_purchases_edi_import(file_io, "edi.xlsx")

    assert "OK" in result
    rows = excel_io(file_io)
    assert rows[0][0] == "ACHATS FOURNISSEUR IMPORT EDI"
    data = next(row for row in rows[4:] if row[2] == "FOUR001")
    assert data[4] == "AVOIR"
    assert data[8] == "AF0001"
    assert data[14] == "E1"
    assert data[25:30] == ["CAHA", "OPT", "NAF", "FR", "NAF"]
    assert data[30:32] == ["Marchandises", "Montures"]


def test_purchases_edi_import_excel_erreur(monkeypatch, caplog):
    def boom(*args, **kwargs):
        raise ValueError("boom")

    with (
        patched_attrs(monkeypatch, generic_list_export, titre_page_writer=boom),
        patched_attrs(monkeypatch, edi_out, titre_page_writer=boom),
        caplog.at_level(logging.ERROR),
    ):
        assert edi_out.excel_heron_purchases_edi_import(io.BytesIO(), "edi.xlsx") == {
            "KO": "ERREUR DANS LA GENERATION DU FICHIER"
        }


@pytest.mark.usefixtures("edi_data")
def test_purchases_edi_import_csv(tmp_path):
    """COPY TO côté serveur (Postgres local, même machine) : fichier csv avec entête et la ligne"""
    emplacement = tmp_path / "achats_edi.csv"

    result = edi_out.csv_heron_purchases_edi_import(emplacement)

    assert "OK" in result
    content = emplacement.read_text(encoding="utf8").splitlines()
    assert content[0].startswith("Centrale;Enseigne;Tiers X3")
    assert len(content) == 2
    assert ";FOUR001;" in content[1]
    assert ";AVOIR;" in content[1]


def test_purchases_edi_import_csv_erreur(tmp_path, caplog):
    emplacement = tmp_path / "absent" / "achats.csv"

    with caplog.at_level(logging.ERROR):
        result = edi_out.csv_heron_purchases_edi_import(emplacement)

    assert result == {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}
    assert "achats.csv" in caplog.text
