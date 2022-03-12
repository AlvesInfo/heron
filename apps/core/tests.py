import io
import sys
from pathlib import Path

base_path = Path(__file__).resolve().parent
sys.path.insert(1, base_path)
sys.path.append(base_path)

# from django.test import TestCase

from apps.core.functions.function_imports import (
    excel_file_to_csv_string_io,
    ExcelToCsvIncompatibleFileError,
)


file_test_txt = base_path / "test_fixtures/test_pandas.txt"
file_test_csv = base_path / "test_fixtures/test_pandas.csv"
file_test_xls = base_path / "test_fixtures/test_pandas.xls"
file_test_xlsx = base_path / "test_fixtures/test_pandas.xlsx"
file_test_xls_bbgr_01 = base_path / "test_fixtures/DEL_STATMNT_REP_20200531_85585975.xls"
file_test_xls_bbgr_02 = base_path / "test_fixtures/DEL_STATMNT_REP_20210228_96191627.xls"
file_test_xls_bbgr_03 = base_path / "test_fixtures/DEL_STATMNT_REP_20220228_116224869.xls"
file_test_xls_bbgr_04 = base_path / "test_fixtures/ACUITIS_MONTHLY_DEL_REP_20180831_69746151.xls"

csv_string_io = io.StringIO()
try:
    excel_file_to_csv_string_io(file_test_txt, csv_string_io, header=False)
except ExcelToCsvIncompatibleFileError:
    print(f"{file_test_csv}, n'est pas un fichier excel")

try:
    excel_file_to_csv_string_io(file_test_csv, csv_string_io, header=False)
except ExcelToCsvIncompatibleFileError:
    print(f"{file_test_csv}, n'est pas un fichier excel")

try:
    excel_file_to_csv_string_io(file_test_xls, csv_string_io, header=False)
except ExcelToCsvIncompatibleFileError:
    print(f"{file_test_xls}, n'est pas un fichier excel")

try:
    excel_file_to_csv_string_io(file_test_xlsx, csv_string_io, header=False)
except ExcelToCsvIncompatibleFileError:
    print(f"{file_test_xlsx}, n'est pas un fichier excel")

try:
    excel_file_to_csv_string_io(file_test_xls_bbgr_01, csv_string_io, header=False)
except ExcelToCsvIncompatibleFileError:
    print(f"{file_test_xls_bbgr_01}, n'est pas un fichier excel")

try:
    excel_file_to_csv_string_io(file_test_xls_bbgr_02, csv_string_io, header=False)
except ExcelToCsvIncompatibleFileError:
    print(f"{file_test_xls_bbgr_02}, n'est pas un fichier excel")

try:
    excel_file_to_csv_string_io(file_test_xls_bbgr_03, csv_string_io, header=False)
except ExcelToCsvIncompatibleFileError:
    print(f"{file_test_xls_bbgr_03}, n'est pas un fichier excel")

try:
    excel_file_to_csv_string_io(file_test_xls_bbgr_03, csv_string_io, header=False)
except ExcelToCsvIncompatibleFileError:
    print(f"{file_test_xls_bbgr_04}, n'est pas un fichier excel")
