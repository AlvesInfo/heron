# pylint: disable=E0401,W0702,W1203
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
        "width": 30,
    },
    {
        "entete": "Type\nPièce",
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
        "entete": "N° Pièce",
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
        "width": 17,
    },
    {
        "entete": "Date\nPièce",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{"align": "center", "num_format": "dd/mm/yyyy"},
        },
        "width": 10,
    },
    {
        "entete": "Montant\nHT\nPièce",
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
        "entete": "TVA\nPièce",
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
        "entete": "Montant\nTTC\nPièce",
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
        "entete": "CCT\nForun.",
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
        "entete": "CCT\nSage X3",
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
        "entete": "Client",
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
        "entete": "N° BL",
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
        "entete": "Date\nBL",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{"align": "center", "num_format": "dd/mm/yyyy"},
        },
        "width": 10,
    },
    {
        "entete": "Devise",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{"align": "center"},
        },
        "width": 8,
    },
    {
        "entete": "Reférence article",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{"align": "left"},
        },
        "width": 22,
    },
    {
        "entete": "Libellé article",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{"align": "left"},
        },
        "width": 35,
    },
    {
        "entete": "Qty",
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
                "num_format": "#,##0",
            },
        },
        "width": 8,
    },
    {
        "entete": "P.U\nBrut",
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
        "width": 9,
    },
    {
        "entete": "Remise",
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
                "num_format": "#,##0.00 %",
            },
        },
        "width": 9,
    },
    {
        "entete": "P.U\nNet",
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
        "width": 9,
    },
    {
        "entete": "Montant\nNet",
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
        "width": 9,
    },
    {
        "entete": "Taux\nTVA",
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
                "num_format": "#,##0.00 %",
            },
        },
        "width": 9,
    },
    {
        "entete": "Montant\nTVA",
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
        "width": 9,
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
        "width": 9,
    },
    {
        "entete": "AXE\nBU",
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
    {
        "entete": "AXE\nPRJ",
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
    {
        "entete": "AXE\nPRO",
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
    {
        "entete": "AXE\nPYS",
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
    {
        "entete": "AXE\nRFA",
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
    {
        "entete": "Grande Catégorie",
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
    {
        "entete": "Rubrique\nPresta",
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
    {
        "entete": "Prénom",
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
        "width": 15,
    },
    {
        "entete": "Nom",
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
        "width": 15,
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


def excel_invoice_details(file_io: io.BytesIO, file_name: str, attr_dict: dict) -> dict:
    """Fonction de génération du fichier de liste des Tiers, Fournisseurs, Clients"""
    third_party_num = attr_dict.get("third_party_num")
    supplier = attr_dict.get("supplier")
    invoice_month = attr_dict.get("invoice_month")
    month = pendulum.parse(invoice_month).format("MMMM YYYY", locale="fr").capitalize()
    titre = f"{third_party_num} - {supplier} : {month}"

    list_excel = [file_io, ["DETAILS FACTURES"]]
    excel = GenericExcel(list_excel)
    file_path = Path(
        f"{str(APPS_DIR)}/validation_purchases/sql_files/sql_supplier_invoice_details.sql"
    )
    get_clean_rows = [line[: len(COLUMNS)] for line in get_rows(file_path, attr_dict)]

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
            excel, 1, COLUMNS, {"sens": "portrait", "repeat_row": (0, 5), "fit_page": (1, 0)}
        )

    except:
        LOGGER_EXPORT_EXCEL.exception(f"{file_name!r}")
        return {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}

    finally:
        excel.excel_close()

    return {"OK": f"GENERATION DU FICHIER {file_name} TERMINEE AVEC SUCCES"}
