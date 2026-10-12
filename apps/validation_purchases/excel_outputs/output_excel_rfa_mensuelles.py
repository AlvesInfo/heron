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

from apps.core.functions.functions_setups import settings, connection
from apps.core.excel_outputs.excel_writer import (
    f_entetes,
    f_ligne,
)
from apps.rfa.models import SupplierRate
from apps.validation_purchases.excel_outputs.columns_excel import (
    columns_rfa_mensuelles,
    columns_rfa_cct,
    columns_rfa_signboard,
)
from apps.core.excel_outputs.generic_list_export import SheetSpec, excel_sheets_export, write_alternate_rows



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


TOTAL_COLOR = {"bg_color": "#dce7f5", "bold": True}
TOTAL_LABEL_FORMAT = {"font_size": 10, "font_name": "Calibri", "valign": "top", "bottom": 1, "top": 1}
# Feuille détail : seules ces colonnes de montants (rang parmi les montants) sont totalisées
DETAIL_SUMMED_RANKS = {1, 4, 5}


def total_formats(columns, nb_labels: int) -> list[dict]:
    """Formats de la ligne TOTAL : libellés encadrés à gauche et à droite, puis formats des montants"""
    borders = {0: {"left": 1}, nb_labels - 1: {"right": 1, "align": "right"}}
    labels = [{**TOTAL_LABEL_FORMAT, **borders.get(j, {}), **TOTAL_COLOR} for j in range(nb_labels)]
    amounts = [{**column.get("f_ligne").copy(), **TOTAL_COLOR} for column in columns[nb_labels:]]

    return labels + amounts


def write_sum(excel, sheet, debut, row, columns, nb_sums):
    """Écrit la ligne TOTAL (sommes des nb_sums dernières colonnes) et renvoie la ligne suivante"""
    nb_labels = len(columns) - nb_sums
    totaux = [""] * (nb_labels - 1) + ["TOTAL"]

    for rank, col in enumerate(range(nb_labels, len(columns)), 1):
        summed = sheet != 1 or rank in DETAIL_SUMMED_RANKS
        totaux.append(
            f"=SUM({xl_rowcol_to_cell(debut, col)}:{xl_rowcol_to_cell(row - 1, col)})" if summed else ""
        )

    excel.write_rows(sheet, row, 0, totaux, total_formats(columns, nb_labels))

    return row + 1


def board_writer(nb_sums):
    """Écriture des lignes puis de la ligne TOTAL, pour une feuille de nb_sums colonnes de montants"""

    def _write(excel, sheet, columns, rows, f_lignes, f_lignes_odd):
        row = 4
        count = write_alternate_rows(excel, sheet, row, rows, f_lignes, f_lignes_odd)
        write_sum(excel, sheet, row, row + count, columns, nb_sums)

    return _write


def excel_rfa_mensuelles(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier de liste des RFA mensuelles (détail, par clients, par enseignes)"""
    sheets_dict = {
        "DETAILS RFA": ("DETAILS RFA", get_rows),
        "PAR CLIENTS": ("RFA MENSUELLES PAR CLIENTS", get_rows_resume_cct),
        "PAR ENSEIGNES": ("RFA MENSUELLES PAR ENSEIGNES", get_rows_resume_signboard),
    }
    specs = []

    for name, (titre, get_rows_func) in sheets_dict.items():
        nb_sums, columns, rows = get_rows_func()
        specs.append(
            SheetSpec(
                name=name, title=titre, columns=columns, rows=rows, odd_color="#F0F0F0",
                writer=board_writer(nb_sums), extra_formatting={"not_display_zero": True},
            )
        )

    return excel_sheets_export(file_io, file_name, specs, in_memory=True)
