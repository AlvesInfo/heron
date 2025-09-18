# pylint: disable=W0702,W1203
"""Module d'export du fichier excel pour les cumuls de factures intégrées pas tiers, mois, cétégorie

Commentaire:

created at: 2022-05-12
created by: Paulo ALVES

modified at: 2022-05-12
modified by: Paulo ALVES
"""
import io
from typing import Dict
from pathlib import Path

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

COLUMNS = [
    {
        "entete": "Tiers X3",
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
        "width": 8,
    },
    {
        "entete": "Type",
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
        "width": 8,
    },
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
        "width": 31,
    },
    {
        "entete": "Montant\nHT",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "right",
                "num_format": "#,##0.00",
            },
        },
        "width": 10.6,
    },
    {
        "entete": "Montant\nTTC",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "right",
                "num_format": "#,##0.00",
            },
        },
        "width": 10.6,
    },
    {
        "entete": "Nbre de\nFactures",
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
                "num_format": "#,##0",
            },
        },
        "width": 8,
    },
    {
        "entete": "Mois des\nFactues",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{"align": "center", "num_format": "mmmm yyyy"},
        },
        "width": 13,
    },
    {
        "entete": "",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#FFC000",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "center",
                "bg_color": "#FFC000",
            },
        },
        "width": 1,
    },
    {
        "entete": "Relevé\nMontant\nHT",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "right",
                "num_format": "#,##0.00",
            },
        },
        "width": 10.6,
    },
    {
        "entete": "Relevé\nMontant\nTTC",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "right",
                "num_format": "#,##0.00",
            },
        },
        "width": 10.6,
    },
    {
        "entete": "",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#FFC000",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "right",
                "bg_color": "#FFC000",
            },
        },
        "width": 1,
    },
    {
        "entete": "Ecart\nHT",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "right",
                "bold": True,
                "num_format": "#,##0.00",
            },
        },
        "width": 10,
    },
    {
        "entete": "Ecart\nTTC",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "right",
                "bold": True,
                "num_format": "#,##0.00",
            },
        },
        "width": 10.6,
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
            **{
                "align": "left",
                "text_wrap": True,
            },
        },
        "width": 80,
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
        # print(cursor.mogrify(query).decode())
        # print(query)
        cursor.execute(query, parmas_dict)
        return cursor.fetchall()


def excel_integration_purchases(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier de liste des Tiers, Fournisseurs, Clients"""
    titre_list = file_name.split("_")
    titre = " ".join(titre_list[:3])
    list_excel = [file_io, [titre]]
    excel = GenericExcel(list_excel)
    excel.sheet_hide_zero(0)
    file_path = Path(
        f"{str(APPS_DIR)}/validation_purchases/sql_files/sql_integration_purchases.sql"
    )
    get_clean_rows = [line[:len(COLUMNS)] for line in get_rows(file_path)]

    try:
        titre_page_writer(excel, 1, 0, 0, COLUMNS, titre)
        output_day_writer(excel, 1, 1, 0)
        columns_headers_writer(excel, 1, 3, 0, COLUMNS)
        f_lignes = [dict_row.get("f_ligne") for dict_row in COLUMNS]
        f_lignes_odd = [
            dict_row.get("f_ligne")
            if i in {7, 10}
            else {**dict_row.get("f_ligne"), **{"bg_color": "#D8E4BC"}}
            for i, dict_row in enumerate(COLUMNS)
        ]
        rows_writer(excel, 1, 4, 0, get_clean_rows, f_lignes, f_lignes_odd)
        sheet_formatting(
            excel, 1, COLUMNS, {"sens": "landscape", "repeat_row": (0, 5), "fit_page": (1, 0)}
        )

    except:
        LOGGER_EXPORT_EXCEL.exception(f"{file_name!r}")
        return {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}

    finally:
        excel.excel_close()

    return {"OK": f"GENERATION DU FICHIER {file_name} TERMINEE AVEC SUCCES"}
