"""Tests des exports Excel des dictionnaires entêtes / axes de détails"""
import io
import logging

import openpyxl
import pytest

from apps.invoices.excel_outputs import output_excel_axes_details_list, output_excel_entetes_details_list
from apps.core.excel_outputs import generic_list_export
from conftest import patched_attrs

pytestmark = pytest.mark.django_db


def read_sheet(file_io):
    file_io.seek(0)
    return [[cell.value for cell in row] for row in openpyxl.load_workbook(file_io).worksheets[0].iter_rows()]


def test_excel_entetes_details(make_entete_details):
    make_entete_details("Montures", 1)
    make_entete_details("Verres", 2)
    file_io = io.BytesIO()

    result = output_excel_entetes_details_list.excel_liste_entetes_details(file_io, "ENTETES_DETAILS_2026_1_31_1.xlsx")

    assert "OK" in result
    rows = read_sheet(file_io)
    assert rows[0][0] == "ENTETES DETAILS"
    assert [row[1] for row in rows if row[0] in ("1", "2")] == ["Montures", "Verres"]


def test_excel_axes_details(make_axes_details):
    make_axes_details("OPT", "Montures")
    file_io = io.BytesIO()

    result = output_excel_axes_details_list.excel_liste_axes_details(file_io, "AXES_DETAILS_2026_1_31_1.xlsx")

    assert "OK" in result
    assert any(row[1] == "Montures" and "OPT" in str(row[0]) for row in read_sheet(file_io))


@pytest.mark.parametrize(
    ("module", "function"),
    [
        (output_excel_entetes_details_list, "excel_liste_entetes_details"),
        (output_excel_axes_details_list, "excel_liste_axes_details"),
    ],
)
def test_excel_erreur(module, function, monkeypatch, caplog):
    def boom(*args, **kwargs):
        raise ValueError("boom")

    with patched_attrs(monkeypatch, generic_list_export, titre_page_writer=boom), patched_attrs(monkeypatch, module, titre_page_writer=boom), caplog.at_level(logging.ERROR):
        result = getattr(module, function)(io.BytesIO(), "X_1_2_3_4.xlsx")

    assert result == {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}
