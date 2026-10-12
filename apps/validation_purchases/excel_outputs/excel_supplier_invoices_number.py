"""Module d'export du fichier excel pour les factures du tiers pas mois.

Commentaire:

created at: 2022-05-12
created by: Paulo ALVES

modified at: 2022-05-12
modified by: Paulo ALVES
"""

import io
from pathlib import Path

from django.conf import settings
from django.db import connection

from apps.core.excel_outputs.excel_writer import (
    f_entetes,
    f_ligne,
)
from apps.core.excel_outputs.generic_list_export import excel_list_export

COLUMNS = [
    {
        "entete": "Tiers X3",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "center",
        },
        "width": 8,
    },
    {
        "entete": "Fournisseur",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "left",
        },
        "width": 30,
    },
    {
        "entete": "Type\nPièce",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "center",
        },
        "width": 10,
    },
    {
        "entete": "N° Pièce",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "center",
        },
        "width": 15,
    },
    {
        "entete": "Date\nPièce",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "center",
            "num_format": "dd/mm/yyyy",
        },
        "width": 10,
    },
    {
        "entete": "Montant\nHT\nPièce",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "right",
            "num_format": "#,##0.00",
        },
        "width": 10.6,
    },
    {
        "entete": "TVA\nPièce",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "right",
            "num_format": "#,##0.00",
        },
        "width": 10.6,
    },
    {
        "entete": "Montant\nTTC\nPièce",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "right",
            "num_format": "#,##0.00",
        },
        "width": 10.6,
    },
    {
        "entete": "CCT\nForun.",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "center",
        },
        "width": 8,
    },
    {
        "entete": "CCT\nSage X3",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "center",
        },
        "width": 8,
    },
    {
        "entete": "Client",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "left",
        },
        "width": 31,
    },
    {
        "entete": "N° BL",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "center",
        },
        "width": 15,
    },
    {
        "entete": "Date\nBL",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "center",
            "num_format": "dd/mm/yyyy",
        },
        "width": 10,
    },
    {
        "entete": "Devise",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "center",
        },
        "width": 8,
    },
    {
        "entete": "Reférence article",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "left",
        },
        "width": 22,
    },
    {
        "entete": "Libellé article",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "left",
        },
        "width": 35,
    },
    {
        "entete": "Qty",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "right",
            "num_format": "#,##0",
        },
        "width": 8,
    },
    {
        "entete": "P.U\nBrut",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "right",
            "num_format": "#,##0.00",
        },
        "width": 9,
    },
    {
        "entete": "Remise",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "right",
            "num_format": "#,##0.00 %",
        },
        "width": 9,
    },
    {
        "entete": "P.U\nNet",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "right",
            "num_format": "#,##0.00",
        },
        "width": 9,
    },
    {
        "entete": "Montant\nNet",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "right",
            "num_format": "#,##0.00",
        },
        "width": 9,
    },
    {
        "entete": "Taux\nTVA",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "right",
            "num_format": "#,##0.00 %",
        },
        "width": 9,
    },
    {
        "entete": "Montant\nTVA",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "right",
            "num_format": "#,##0.00",
        },
        "width": 9,
    },
    {
        "entete": "Montant\nTTC",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "right",
            "num_format": "#,##0.00",
        },
        "width": 9,
    },
    {
        "entete": "AXE\nBU",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "center",
        },
        "width": 12,
    },
    {
        "entete": "AXE\nPRJ",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "center",
        },
        "width": 12,
    },
    {
        "entete": "AXE\nPRO",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "center",
        },
        "width": 12,
    },
    {
        "entete": "AXE\nPYS",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "center",
        },
        "width": 12,
    },
    {
        "entete": "AXE\nRFA",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "center",
        },
        "width": 12,
    },
    {
        "entete": "Grande Catégorie",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "center",
        },
        "width": 12,
    },
    {
        "entete": "Rubrique\nPresta",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "center",
        },
        "width": 12,
    },
    {
        "entete": "Prénom",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
        },
        "width": 15,
    },
    {
        "entete": "Nom",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
        },
        "width": 15,
    },
]


def get_rows(file_path: Path, parmas_dict: dict | None = None):
    """Renvoie les résultats de la requête nécessaire à l'export excel.

    :param file_path: file pathlib.PATH
    :param parmas_dict: paramètre de la requête
    :return: resultats de la requête.
    """
    parmas_dict = parmas_dict or {}

    with file_path.open("r") as sql_file, connection.cursor() as cursor:
        query = sql_file.read()
        cursor.execute(query, parmas_dict)
        return cursor.fetchall()


def excel_invoice_number(file_io: io.BytesIO, file_name: str, attr_dict: dict) -> dict:
    """Fonction de génération du fichier de liste des Tiers, Fournisseurs, Clients."""
    third_party_num = attr_dict.get("third_party_num")
    supplier = attr_dict.get("supplier")
    invoice_number = attr_dict.get("invoice_number")
    titre = f"{third_party_num} - {supplier} : Pièce N° {invoice_number}"
    file_path = Path(f"{settings.APPS_DIR!s}/validation_purchases/sql_files/sql_invoice_number.sql")
    get_clean_rows = [line[: len(COLUMNS)] for line in get_rows(file_path, attr_dict)]

    return excel_list_export(
        file_io,
        file_name,
        sheet_name="FACTURE ",
        title=titre,
        columns=COLUMNS,
        rows=get_clean_rows,
    )
