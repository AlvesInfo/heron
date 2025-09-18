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
        "entete": "tiers X3",
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
        "width": 10,
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
        "width": 9,
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
        "width": 20,
    },
    {
        "entete": "Mois facture",
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
                "num_format": "mmmm yyyy",
            },
        },
        "width": 12,
    },
    {
        "entete": "factures",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{"align": "left", "text_wrap": True},
        },
        "width": 80,
    },
    {
        "entete": "Référence Article",
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
        "width": 20,
    },
    {
        "entete": "Axe RFA",
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
        "width": 12,
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
        return [row[1:9] for row in cursor.fetchall()]


def control_rfa_period_excel(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier de l'étape 3.6 - Contrôle période RFA"""
    titre = "3.6 - Contrôle période RFA"
    list_excel = [file_io, ["RFA"]]
    excel = GenericExcel(list_excel, in_memory=True)
    file_path = Path(f"{str(APPS_DIR)}/validation_purchases/sql_files/sql_control_rfa_period.sql")
    get_clean_rows = [row[:-1] for row in get_rows(file_path)]

    try:
        titre_page_writer(excel, 1, 0, 0, COLUMNS, titre)
        output_day_writer(excel, 1, 1, 0)
        columns_headers_writer(excel, 1, 3, 0, COLUMNS)
        f_lignes = [dict_row.get("f_ligne") for dict_row in COLUMNS]
        f_lignes_odd = [
            {**dict_row.get("f_ligne"), **{"bg_color": "#D9D9D9"}} for dict_row in COLUMNS
        ]
        rows_writer(excel, 1, 4, 0, get_clean_rows, f_lignes, f_lignes_odd)
        sheet_formatting(
            excel, 1, COLUMNS, {"sens": "landscape", "repeat_row": (0, 3), "fit_page": (1, 0)}
        )

    except:
        LOGGER_EXPORT_EXCEL.exception(f"{file_name!r}")
        return {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}

    finally:
        excel.excel_close()

    return {"OK": f"GENERATION DU FICHIER {file_name} TERMINEE AVEC SUCCES"}
