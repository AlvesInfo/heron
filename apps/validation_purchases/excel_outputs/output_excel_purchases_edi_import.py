# pylint: disable=W0702,W1203,E0401,E1101,C0103,W0603
"""Module d'export du fichier excel des achats Héron non finalisées

Commentaire:

created at: 2023-06-20
created by: Paulo ALVES

modified at: 2023-06-20
modified by: Paulo ALVES
"""
import io
from pathlib import Path

from psycopg2 import sql

from heron.loggers import LOGGER_EXPORT_EXCEL
from heron.settings import MEDIA_EXCEL_FILES_DIR
from apps.core.functions.functions_setups import settings, connection
from apps.core.functions.functions_excel import GenericExcel
from apps.core.excel_outputs.excel_writer import (
    titre_page_writer,
    output_day_writer,
    columns_headers_writer,
    sheet_formatting,
)
from apps.validation_purchases.excel_outputs.columns_excel import columns_purchases_edi

num_ligne = 0


def get_clean_rows():
    """Retourne les lignes à écrire"""

    sql_file = Path(settings.APPS_DIR) / "validation_purchases/sql_files/sql_current_purchases.sql"

    with connection.cursor() as cursor, sql_file.open("r") as sql_file:
        # print(cursor.mogrify(sql.SQL(sql_file.read())))
        cursor.execute(sql.SQL(sql_file.read()))

        return cursor.fetchall()


def write_board(excel, sheet, clean_rows, f_lignes, f_lignes_odd):
    """
    Ecriture sur la feuille excel des lignes
    :param excel: worksheet
    :param sheet: N° de la feuille excel
    :param clean_rows: lignes à écrire dans la feuille
    :param f_lignes: formatage des lignes paires
    :param f_lignes_odd: formatage des lignes impaires
    """
    global num_ligne
    col = 0

    for clean_row in clean_rows:
        excel.write_rows(
            sheet, num_ligne, col, clean_row, f_lignes if num_ligne % 2 == 0 else f_lignes_odd
        )
        num_ligne += 1


def excel_heron_purchases_edi_import(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier de liste achats fournisseurs imports edi"""
    titre = "ACHATS FOURNISSEUR IMPORT EDI"
    list_excel = [file_io, ["ACHATS FOURNISSEURS"]]
    excel = GenericExcel(list_excel, in_memory=True)
    columns = columns_purchases_edi
    global num_ligne

    try:
        titre_page_writer(excel, 1, 0, 0, columns, titre)
        output_day_writer(excel, 1, 1, 0)
        columns_headers_writer(excel, 1, 3, 0, columns)
        f_lignes = [dict_row.get("f_ligne") for dict_row in columns]
        f_lignes_odd = [
            {**dict_row.get("f_ligne"), **{"bg_color": "#D9D9D9"}} for dict_row in columns
        ]
        num_ligne = 4
        sheet = 1
        write_board(excel, sheet, get_clean_rows(), f_lignes, f_lignes_odd)
        sheet_formatting(
            excel, 1, columns, {"sens": "portrait", "repeat_row": (0, 5), "fit_page": (1, 0)}
        )

    except:
        LOGGER_EXPORT_EXCEL.exception(f"{file_name!r}")
        return {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}

    finally:
        excel.excel_close()

    return {"OK": f"GENERATION DU FICHIER {file_name} TERMINEE AVEC SUCCES"}


def csv_heron_purchases_edi_import(emplacement: Path) -> dict:
    """Fonction de génération du fichier csvde liste achats fournisseurs imports edi"""

    try:

        sql_file = (
            Path(settings.APPS_DIR) / "validation_purchases/sql_files/sql_current_purchases_csv.sql"
        )

        with connection.cursor() as cursor, sql_file.open("r") as sql_file:
            # print(cursor.mogrify(sql.SQL(sql_file.read())))
            cursor.execute(sql.SQL(sql_file.read()), {"to_csv": str(emplacement)})

    except:
        LOGGER_EXPORT_EXCEL.exception(f"{emplacement.name!r}")
        return {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}

    return {"OK": f"GENERATION DU FICHIER {emplacement.name} TERMINEE AVEC SUCCES"}
