# pylint: disable=E0401,W0702,W1203,R0914
"""Module d'export du fichier excel pour les factures du tiers pas mois

Commentaire:

created at: 2022-05-12
created by: Paulo ALVES

modified at: 2022-05-12
modified by: Paulo ALVES
"""
import io
from typing import Dict
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
    rows_writer,
)

COLUMNS_TITRES = [
    {
        "entete": "M",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
    },
    {
        "entete": "M1",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
    },
    {
        "entete": "TRIMESTRE GLISSANT",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
    },
    {
        "entete": "12 MOIS GLISSANTS",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
    },
]

COLUMNS = [
    {
        "entete": "Enseigne",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "center",
            },
        },
        "width": 15,
    },
    {
        "entete": "Pays",
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
        "width": 14,
    },
    {
        "entete": "CCT",
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
        "width": 12,
    },
    {
        "entete": "Nom Client",
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
        "width": 25,
    },
    {
        "entete": "CA\nCOSIUM\nHT",
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
        "width": 11,
    },
    {
        "entete": "VENTES\nHERON\nHT",
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
        "width": 11,
    },
    {
        "entete": "Taux\nAchats",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "num_format": "#,##0.00%",
            },
        },
        "width": 11,
    },
    {
        "entete": "CA\nCOSIUM\nHT",
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
        "width": 11,
    },
    {
        "entete": "VENTES\nHERON\nHT",
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
        "width": 11,
    },
    {
        "entete": "Taux\nAchats",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "num_format": "#,##0.00%",
            },
        },
        "width": 11,
    },
    {
        "entete": "CA\nCOSIUM\nHT",
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
        "width": 11,
    },
    {
        "entete": "VENTES\nHERON\nHT",
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
        "width": 11,
    },
    {
        "entete": "Taux\nAchats",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "num_format": "#,##0.00%",
            },
        },
        "width": 11,
    },
    {
        "entete": "CA\nCOSIUM\nHT",
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
        "width": 11,
    },
    {
        "entete": "VENTES\nHERON\nHT",
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
        "width": 11,
    },
    {
        "entete": "Taux\nAchats",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "num_format": "#,##0.00%",
            },
        },
        "width": 11,
    },
    {
        "entete": "Commentaire",
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


def excel_ca_cct(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de 5.3 - Contrôle CA Cosium / Ventes Héron"""
    titre = "5.3 - Contrôle CA Cosium / Ventes Héron"
    list_excel = [file_io, ["CA CCT"]]
    excel = GenericExcel(list_excel, in_memory=True)
    file_path = Path(f"{str(APPS_DIR)}/validation_purchases/sql_files/sql_ca_cct.sql")
    mois = 1

    for i, column_dict in enumerate(COLUMNS_TITRES, 1):
        if i < 3:
            column_dict["entete"] = (
                (
                    pendulum.now()
                    .subtract(months=mois)
                    .start_of("month")
                    .format("MMMM YYYY", locale="fr")
                )
                .upper()
            )
            mois += 1

    try:
        titre_page_writer(excel, 1, 0, 0, COLUMNS, titre)
        output_day_writer(excel, 1, 1, 0)
        row = 3
        col = 4
        for entete_dict in COLUMNS_TITRES:
            excel.write_merge_h(
                1, row, col, col + 2, entete_dict.get("entete"), style=entete_dict.get("f_entete")
            )
            col += 3

        row += 1
        columns_headers_writer(excel, 1, row, 0, COLUMNS)

        f_lignes = [dict_row.get("f_ligne") for dict_row in COLUMNS]
        f_lignes_odd = [
            {**dict_row.get("f_ligne"), **{"bg_color": "#D9D9D9"}} for dict_row in COLUMNS
        ]

        row += 1
        rows_writer(excel, 1, row, 0, get_rows(file_path), f_lignes, f_lignes_odd)
        sheet_formatting(
            excel, 1, COLUMNS, {"sens": "portrait", "repeat_row": (0, 3), "fit_page": (1, 0)}
        )

    except:
        LOGGER_EXPORT_EXCEL.exception(f"{file_name!r}")
        return {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}

    finally:
        excel.excel_close()

    return {"OK": f"GENERATION DU FICHIER {file_name} TERMINEE AVEC SUCCES"}
