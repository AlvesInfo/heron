# pylint: disable=W0702,W1203,E0401,E1101,C0103,W0603
# ruff: noqa: E722
"""Module d'export du fichier excel des achats Héron non finalisées

Commentaire:

created at: 2024-08-09
created by: Paulo ALVES

modified at: 2024-08-09
modified by: Paulo ALVES
"""

import io
from pathlib import Path

from psycopg2 import sql
from xlsxwriter.utility import xl_rowcol_to_cell

from heron.loggers import LOGGER_EXPORT_EXCEL
from apps.core.functions.functions_setups import settings, connection
from apps.core.functions.functions_excel import GenericExcel
from apps.core.excel_outputs.excel_writer import (
    titre_page_writer,
    output_day_writer,
    columns_headers_writer,
    sheet_formatting,
    f_entetes,
    f_ligne,
)
from apps.rfa.models import SupplierRate
from apps.validation_purchases.excel_outputs.columns_excel import (
    columns_rfa_mensuelles,
    columns_rfa_cct,
    columns_rfa_signboard,
)

num_ligne = 0


def get_amounts_sql():
    """Retourne un tuple des textes des montants, pour chaque fournisseur"""
    suppliers_list = SupplierRate.objects.all().values_list("supplier", flat=True)
    sum_amount_sql_suppliers = ""
    amount_sql_suppliers = ""
    base_column_dict = {
        "entete": "",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "num_format": "#,##0.00",
            },
        },
        "width": 10,
    }
    columns_list = []
    nb_sums = 0

    for supplier in suppliers_list:
        sum_amount_sql_suppliers += f"""
        sum("{supplier}") as "{supplier}","""
        amount_sql_suppliers += f"""
        case
            when "ee"."third_party_num" = '{supplier}'
            then "ee"."net_amount"
            else 0
        end as "{supplier}","""
        column_dict = {**base_column_dict, "entete": supplier}
        columns_list.append(column_dict)
        nb_sums += 1

    column_dict = {**base_column_dict, "entete": "Total HT"}
    columns_list.append(column_dict)
    nb_sums += 1

    return nb_sums, sum_amount_sql_suppliers, amount_sql_suppliers, columns_list


def get_rows():
    """Retourne les lignes à écrire"""

    sql_file = (
        Path(settings.APPS_DIR)
        / "validation_purchases/sql_files/sql_rfa_mensuelles.sql"
    )

    with connection.cursor() as cursor, sql_file.open("r") as sql_file:
        # print(cursor.mogrify(sql.SQL(sql_file.read())).decode())
        cursor.execute(sql.SQL(sql_file.read()))
        nb_sums = 14
        return nb_sums, columns_rfa_mensuelles, cursor.fetchall()


def get_rows_resume_cct():
    """Retourne les lignes à écrire"""

    sql_file = (
        Path(settings.APPS_DIR)
        / "validation_purchases/sql_files/sql_rfa_mensuelles_resume_cct.sql"
    )
    nb_sums, sum_amount_sql_suppliers, amount_sql_suppliers, columns_list = (
        get_amounts_sql()
    )
    with connection.cursor() as cursor, sql_file.open("r") as sql_file:
        sql_text = (
            sql_file.read()
            .replace("$sum_amount_sql_suppliers$", sum_amount_sql_suppliers)
            .replace("$amount_sql_suppliers$", amount_sql_suppliers)
        )
        # print(cursor.mogrify(sql.SQL(sql_text)).decode())
        cursor.execute(sql.SQL(sql_text))

        return nb_sums, [*columns_rfa_cct, *columns_list], cursor.fetchall()


def get_rows_resume_signboard():
    """Retourne les lignes à écrire"""

    sql_file = (
        Path(settings.APPS_DIR)
        / "validation_purchases/sql_files/sql_rfa_mensuelles_resume_signboard.sql"
    )
    nb_sums, sum_amount_sql_suppliers, amount_sql_suppliers, columns_list = (
        get_amounts_sql()
    )
    with connection.cursor() as cursor, sql_file.open("r") as sql_file:
        sql_text = (
            sql_file.read()
            .replace("$sum_amount_sql_suppliers$", sum_amount_sql_suppliers)
            .replace("$amount_sql_suppliers$", amount_sql_suppliers)
        )
        # print(cursor.mogrify(sql.SQL(sql_text)).decode())
        cursor.execute(sql.SQL(sql_text))

        return nb_sums, [*columns_rfa_signboard, *columns_list], cursor.fetchall()


def write_sum(excel, sheet, debut, columns, nb_sums):
    """Ecriture des Sous-Totaux
    :param excel: worksheet
    :param sheet: N° de la feuille excel
    :param debut: Ligne de début de la somme
    """
    global num_ligne
    col = 0
    f_totaux = []
    color_dict = {"bg_color": "#dce7f5", "bold": True}

    common_dict = {
        "font_size": 10,
        "font_name": "Calibri",
        "valign": "top",
        "bottom": 1,
        "top": 1,
    }

    for j, _ in enumerate(columns):
        if j < (len(columns) - nb_sums):
            if j == 0:
                left_right_dict = {"left": 1}
            elif j == (len(columns) - nb_sums + 1):
                left_right_dict = {"right": 1, "align": "right"}
            else:
                left_right_dict = {}

            f_totaux.append({**common_dict, **left_right_dict, **color_dict})

        else:
            f_totaux.append({**columns[j].get("f_ligne").copy(), **color_dict})

    totaux = [""] * (len(columns) - nb_sums - 1) + ["TOTAL"]

    for j, c in enumerate(range(len(columns) - nb_sums, len(f_totaux)), 1):
        if sheet == 1 and j not in {1, 4, 5}:
            totaux.append("")
        else:
            totaux.append(
                f"=SUM({xl_rowcol_to_cell(debut, c)}:{xl_rowcol_to_cell(num_ligne - 1, c)})"
            )

    excel.write_rows(sheet, num_ligne, col, totaux, f_totaux)
    num_ligne += 1


def write_board(excel, sheet, clean_rows, f_lignes, f_lignes_odd, columns, nb_sums):
    """
    Ecriture sur la sheet excel des lignes
    :param excel: worksheet
    :param sheet: N° de la sheet excel
    :param clean_rows: lignes à écrire dans la sheet
    :param f_lignes: formatage des lignes paires
    :param f_lignes_odd: formatage des lignes impaires
    :param columns: colonnes
    :param nb_sums: nbre de fournisseurs
    """
    global num_ligne
    col = 0
    debut = num_ligne

    for clean_row in clean_rows:
        excel.write_rows(
            sheet,
            num_ligne,
            col,
            clean_row,
            f_lignes if num_ligne % 2 == 0 else f_lignes_odd,
        )
        num_ligne += 1

    write_sum(excel, sheet, debut, columns, nb_sums)


def excel_rfa_mensuelles(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier de liste des RFA mensuelles"""
    list_excel = [file_io, ["DETAILS RFA", "PAR CLIENTS", "PAR ENSEIGNES"]]
    excel = GenericExcel(list_excel, in_memory=True)

    global num_ligne

    try:
        sheets_dict = {
            1: ("DETAILS RFA", get_rows),
            2: ("RFA MENSUELLES PAR CLIENTS", get_rows_resume_cct),
            3: ("RFA MENSUELLES PAR ENSEIGNES", get_rows_resume_signboard),
        }
        for sheet, values_list in sheets_dict.items():
            num_ligne = 0
            titre, get_rows_func = values_list
            nb_sums, columns, rows = get_rows_func()
            titre_page_writer(excel, sheet, 0, 0, columns, titre)
            output_day_writer(excel, sheet, 1, 0)
            columns_headers_writer(excel, sheet, 3, 0, columns)
            f_lignes = [dict_row.get("f_ligne") for dict_row in columns]
            f_lignes_odd = [
                {**dict_row.get("f_ligne"), **{"bg_color": "#F0F0F0"}}
                for dict_row in columns
            ]
            num_ligne = 4
            write_board(excel, sheet, rows, f_lignes, f_lignes_odd, columns, nb_sums)
            sheet_formatting(
                excel,
                sheet,
                columns,
                {
                    "sens": "portrait",
                    "repeat_row": (0, 5),
                    "fit_page": (1, 0),
                    "not_display_zero": True,
                },
            )

    except:
        LOGGER_EXPORT_EXCEL.exception(f"{file_name!r}")
        return {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}

    finally:
        excel.excel_close()

    return {"OK": f"GENERATION DU FICHIER {file_name} TERMINEE AVEC SUCCES"}
