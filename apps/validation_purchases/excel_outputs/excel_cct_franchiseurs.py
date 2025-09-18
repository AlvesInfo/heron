# pylint: disable=E0401,W0702,W1203
"""Module d'export du fichier excel du Contrôle des achats
des CCT franchiseur (CAHA, MARK, INFO, etc…)

Commentaire:

created at: 2023-07-03
created by: Paulo ALVES

modified at: 2023-07-03
modified by: Paulo ALVES
"""
import io
from typing import Dict, List, Generator
from pathlib import Path

import pendulum
from django.db import connection
from heron.settings.base import APPS_DIR
from heron.loggers import LOGGER_EXPORT_EXCEL
from apps.core.functions.functions_excel import GenericExcel
from apps.core.excel_outputs.excel_writer import (
    f_entetes,
    f_ligne,
    titre_page_writer,
    output_day_writer,
    columns_headers_writer,
    sheet_formatting,
)

COLUMNS = [
    {
        "entete": "Fournisseur",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "left",
            },
        },
        "width": 51,
    },
    {
        "entete": "M-11",
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
    },
    {
        "entete": "M-10",
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
    },
    {
        "entete": "M-9",
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
    },
    {
        "entete": "M-8",
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
    },
    {
        "entete": "M-7",
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
    },
    {
        "entete": "M-6",
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
    },
    {
        "entete": "M-5",
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
    },
    {
        "entete": "M-4",
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
    },
    {
        "entete": "M-3",
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
    },
    {
        "entete": "M-2",
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
    },
    {
        "entete": "M-1",
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
    },
    {
        "entete": "M",
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
    },
    {
        "entete": "Total des 6\nderniers mois",
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
        "width": 14,
    },
    {
        "entete": "Commentaires",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{},
        },
        "width": 50,
    },
]


def get_rows(file_path: Path, parmas_dict: Dict = None):
    """Renvoie les résultats de la requête nécessaire à l'export excel
    :param file_path: file pathlib.PATH
    :param parmas_dict: paramètre de la requête
    :return: resultats de la requête
    """
    parmas_dict = parmas_dict or {}

    with file_path.open("r") as sql_file, connection.cursor() as cursor:
        query = sql_file.read()
        # print(cursor.mogrify(query, parmas_dict).decode())
        # LOGGER_EXPORT_EXCEL.exception(f"{cursor.mogrify(query).decode()!r}")
        # print(query)
        cursor.execute(query, parmas_dict)
        return cursor.fetchall()


def write_rows(excel: GenericExcel, f_lignes: List, f_lignes_odd: List, get_clean_rows: Generator):
    """Ecritures de lignes d'entete des clients"""
    row = 2
    row_format = 1
    col = 0
    current_client = ""
    page_breaks = []

    format_client = {
        "font_name": "calibri",
        "bg_color": "#dce7f5",
        "top": 2,
        "bottom": 1,
        "left": 2,
        "right": 2,
        "bold": True,
        "text_wrap": True,
        "align": "left",
        "valign": "vcenter",
    }

    for rows in get_clean_rows:
        client, *line = rows

        if current_client != client:
            if row > 4:
                row += 1
                page_breaks.append(row)
            else:
                row += 1

            excel.write_row(1, row, col, client, format_client)
            row += 1
            columns_headers_writer(excel, 1, row, 0, COLUMNS)
            current_client = client
            row += 1
            row_format = 1

        excel.write_rows(1, row, col, line, f_lignes if row_format % 2 == 0 else f_lignes_odd)
        row += 1
        row_format += 1

    return page_breaks


def excel_cct_franchiseurs(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier de liste des Tiers, Fournisseurs, Clients"""
    titre = "3.2 - Contrôle des CCT/franchiseurs (MARK, INFO, etc…)"
    list_excel = [file_io, ["CCT - FRANCHISEURS"]]
    excel = GenericExcel(list_excel)
    file_path = Path(f"{str(APPS_DIR)}/validation_purchases/sql_files/sql_cct_franchiseur.sql")

    try:
        mois = 12

        for i, column_dict in enumerate(COLUMNS, 1):
            if 1 < i < 14:
                column_dict["entete"] = (
                    (
                        pendulum.now()
                        .subtract(months=mois)
                        .start_of("month")
                        .format("MMMM YYYY", locale="fr")
                    )
                    .capitalize()
                    .replace(" ", "\n")
                )
                mois -= 1

        titre_page_writer(excel, 1, 0, 0, COLUMNS, titre)
        output_day_writer(excel, 1, 1, 0)
        f_lignes = [dict_row.get("f_ligne") for dict_row in COLUMNS]
        f_lignes_odd = [
            {**dict_row.get("f_ligne"), **{"bg_color": "#D9D9D9"}} for dict_row in COLUMNS
        ]
        page_breaks = write_rows(excel, f_lignes, f_lignes_odd, get_rows(file_path))
        excel.excel_sheet(1).set_h_pagebreaks(page_breaks)
        excel.excel_sheet(1).set_footer("&R&P/&N", {"margin": 0.1})
        sheet_formatting(
            excel, 1, COLUMNS, {"sens": "landscape", "repeat_row": (0, 2), "fit_page": (1, 0)}
        )

    except:
        LOGGER_EXPORT_EXCEL.exception(f"{file_name!r}")
        return {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}

    finally:
        excel.excel_close()

    return {"OK": f"GENERATION DU FICHIER {file_name} TERMINEE AVEC SUCCES"}
