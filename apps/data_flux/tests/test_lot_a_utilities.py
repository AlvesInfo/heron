# pylint: disable=E0401,W0621
"""FR : Tests des utilitaires de data_flux (encodage, conversion excel et fichier en csv StringIO)


EN : Tests for data_flux utilities

created at: 2026-10-11
created by: Paulo ALVES
"""

import io
from pathlib import Path
from typing import ClassVar

import pandas as pd
import pytest
from openpyxl import Workbook

from apps.data_flux import utilities
from apps.data_flux.exceptions import CsvFileToStringIoError, EncodingError, ExcelToCsvFileError
from apps.data_flux.utilities import (
    encoding_detect,
    excel_file_to_csv_string_io,
    file_to_csv_string_io,
)
from conftest import patched_attrs

XLS_FIXTURE = (
    Path(__file__).resolve().parents[2] / "core" / "tests" / "test_fixtures" / "test_pandas.xls"
)


def test_encoding_detect(tmp_path, monkeypatch):
    """Encodage détecté avec confiance, sinon utf8 ; fichier illisible : EncodingError"""
    latin = tmp_path / "latin.txt"
    latin.write_bytes(
        "Déjà vu, été, çà et là, Noël, naïve, forêt, château, garçon\n".encode("latin-1") * 40
    )
    ascii_file = tmp_path / "ascii.txt"
    ascii_file.write_bytes(b"a\n")

    assert encoding_detect(latin).lower() in {"iso-8859-1", "windows-1252", "latin-1"}
    assert encoding_detect(ascii_file) in {"ascii", "utf8"}

    class _Detector:
        done = True
        result: ClassVar[dict] = {"confidence": 0.1, "encoding": "koi8-r"}

        def feed(self, _line):
            """Rien"""

        def close(self):
            """Rien"""

    with patched_attrs(monkeypatch, utilities, UniversalDetector=_Detector):
        assert encoding_detect(ascii_file) == "utf8"

    with pytest.raises(EncodingError, match="absent.txt"):
        encoding_detect(tmp_path / "absent.txt")


def test_excel_file_to_csv_string_io_xlsx(tmp_path):
    """Classeur xlsx : entêtes, entiers sans .0, quoting complet"""
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["code", "coef"])
    sheet.append(["ACF", 1])
    sheet.append(["GAF", 1.5])
    path = tmp_path / "classeur.xlsx"
    workbook.save(path)
    buffer = io.StringIO()

    excel_file_to_csv_string_io(path, buffer)

    assert buffer.getvalue() == '"code";"coef"\n"ACF";"1"\n"GAF";"1.5"\n'
    assert buffer.tell() == 0

    buffer = io.StringIO()
    excel_file_to_csv_string_io(path, buffer, header=False)
    assert buffer.getvalue() == '"ACF";"1"\n"GAF";"1.5"\n'


def test_excel_file_to_csv_string_io_xls_via_xlrd():
    """Un ancien classeur .xls passe par le moteur xlrd"""
    buffer = io.StringIO()

    excel_file_to_csv_string_io(XLS_FIXTURE, buffer)

    assert buffer.getvalue().count("\n") >= 1


def test_excel_file_to_csv_string_io_fichier_non_excel(tmp_path, monkeypatch):
    def _boom(*_args, **_kwargs):
        raise ValueError("Excel file format cannot be determined")

    path = tmp_path / "faux.xlsx"
    path.write_bytes(b"x")
    buffer = io.StringIO()

    with (
        patched_attrs(monkeypatch, pd, read_excel=_boom),
        pytest.raises(ExcelToCsvFileError, match="faux.xlsx"),
    ):
        excel_file_to_csv_string_io(path, buffer)


def test_file_to_csv_string_io(tmp_path, monkeypatch):
    """Encodage fourni ou détecté ; erreur d'encodage et fichier absent en CsvFileToStringIoError"""
    path = tmp_path / "latin.csv"
    path.write_bytes("code;nom\nACF;Aç\n".encode("latin-1"))
    buffer = io.StringIO()

    file_to_csv_string_io(path, buffer, "latin-1")

    assert buffer.getvalue() == "code;nom\nACF;Aç\n"
    assert buffer.tell() == 0

    buffer = io.StringIO()
    file_to_csv_string_io(path, buffer)
    assert buffer.getvalue().startswith("code;nom\n")

    def _boom(_path):
        raise EncodingError("illisible")

    buffer = io.StringIO()
    with (
        patched_attrs(monkeypatch, utilities, encoding_detect=_boom),
        pytest.raises(CsvFileToStringIoError, match="détermination de l'encoding"),
    ):
        file_to_csv_string_io(path, buffer)

    with pytest.raises(CsvFileToStringIoError, match="absent.csv"):
        file_to_csv_string_io(tmp_path / "absent.csv", buffer, "utf8")
