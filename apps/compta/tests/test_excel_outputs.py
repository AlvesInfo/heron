"""Tests des exports Excel des ventes et du CA Cosium"""
import io
import logging
from decimal import Decimal

import openpyxl
import pytest

from apps.compta.excel_outputs import output_excel_ca_cosium, output_excel_sales_cosium
from apps.compta.excel_outputs.output_excel_ca_cosium import excel_ca_cosium
from apps.compta.excel_outputs.output_excel_sales_cosium import excel_sales_cosium
from apps.core.excel_outputs import generic_list_export
from conftest import patched_attrs

pytestmark = pytest.mark.django_db
PERIOD = ("2026-01-01", "2026-01-31")


def read_sheet(file_io: io.BytesIO):
    file_io.seek(0)
    sheet = openpyxl.load_workbook(file_io).worksheets[0]
    return [[cell.value for cell in row] for row in sheet.iter_rows()]


def test_sales_get_clean_rows_sans_maison(make_vente):
    """Une vente non rattachée à une maison ne fait plus planter l'export (None + str)"""
    make_vente(code_cosium="SANS")

    rows = output_excel_sales_cosium.get_clean_rows(*PERIOD)

    assert rows[0][0] == ""
    assert rows[0][3] == " - "
    assert rows[0][2] == "SANS"


def test_excel_sales_cosium(make_vente, make_maison):
    maison = make_maison("AF0001", intitule="Maison Paris")
    make_vente(cct_uuid_identification=maison, id_vente="V1")
    make_vente(cct_uuid_identification=maison, id_vente="V2", date_vente="2026-01-20")
    file_io = io.BytesIO()

    result = excel_sales_cosium(file_io, "ventes.xlsx", *PERIOD)

    assert "OK" in result
    rows = read_sheet(file_io)
    assert rows[0][0].startswith("VENTES COSIUM DU 01/01/2026 AU 31/01/2026")
    data = [row for row in rows if row[1] in ("V1", "V2")]
    assert len(data) == 2
    assert data[0][3] == "AF0001 - Maison Paris"
    assert data[0][0] == "FR"


def test_excel_sales_cosium_erreur(monkeypatch, caplog):
    def boom(*args, **kwargs):
        raise ValueError("boom")

    file_io = io.BytesIO()

    with patched_attrs(monkeypatch, generic_list_export, titre_page_writer=boom), patched_attrs(monkeypatch, output_excel_sales_cosium, titre_page_writer=boom), caplog.at_level(
        logging.ERROR
    ):
        result = excel_sales_cosium(file_io, "ventes.xlsx", *PERIOD)

    assert result == {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}
    assert "ventes.xlsx" in caplog.text


def test_excel_ca_cosium_avec_sous_totaux(make_ca_client, make_maison, make_section, make_country):
    """Deux pays, trois maisons : sous-totaux par maison et totaux par pays"""
    suisse = make_country("CH", "Suisse")
    paris = make_maison("AF0001", intitule="Paris")
    lyon = make_maison("AF0002", intitule="Lyon")
    geneve = make_maison("AF0003", intitule="Genève", pays=suisse)
    opt, aud = make_section("PRO", "OPT"), make_section("PRO", "AUD")
    make_ca_client(maison=paris, axe_pro=opt, ca_ht_eur=Decimal("100"))
    make_ca_client(maison=paris, axe_pro=aud, ca_ht_eur=Decimal("10"))
    make_ca_client(maison=lyon, axe_pro=opt, ca_ht_eur=Decimal("20"))
    make_ca_client(maison=geneve, axe_pro=opt, ca_ht_eur=Decimal("30"))
    file_io = io.BytesIO()

    result = excel_ca_cosium(file_io, "ca.xlsx", *PERIOD)

    assert "OK" in result
    labels = [row[5] for row in read_sheet(file_io) if row[5] and str(row[5]).startswith(("SOUS", "TOTAL"))]
    # Tri par pays (ordre du modèle Country), puis par cct
    assert labels == [
        "SOUS TOTAL AF0001 - Paris", "SOUS TOTAL AF0002 - Lyon", "TOTAL FR",
        "SOUS TOTAL AF0003 - Genève", "TOTAL CH",
    ]


def test_excel_ca_cosium_sans_lignes():
    file_io = io.BytesIO()

    result = excel_ca_cosium(file_io, "ca.xlsx", *PERIOD)

    assert "OK" in result
    assert any("n'a pas été généré" in str(cell) for row in read_sheet(file_io) for cell in row if cell)


@pytest.mark.usefixtures('make_section')
def test_ca_get_clean_rows_sans_maison(make_ca_client):
    ca = make_ca_client()
    ca.cct_uuid_identification = None
    ca.save()

    rows = output_excel_ca_cosium.get_clean_rows(*PERIOD)

    assert rows[0][1] == ""
    assert rows[0][3] == " - "


def test_excel_ca_cosium_erreur(monkeypatch, caplog):
    def boom(*args, **kwargs):
        raise ValueError("boom")

    with patched_attrs(monkeypatch, generic_list_export, titre_page_writer=boom), patched_attrs(monkeypatch, output_excel_ca_cosium, titre_page_writer=boom), caplog.at_level(logging.ERROR):
        result = excel_ca_cosium(io.BytesIO(), "ca.xlsx", *PERIOD)

    assert result == {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}
