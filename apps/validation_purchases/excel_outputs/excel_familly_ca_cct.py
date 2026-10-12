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
from apps.validation_purchases.excel_outputs.excel_ca_cct import merged_month_headers, titres_mois

COLUMNS_TITRES = [
    {
        "entete": "M",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
    },
    {
        "entete": "M1",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
    },
    {
        "entete": "TRIMESTRE GLISSANT",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
    },
    {
        "entete": "12 MOIS GLISSANTS",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
    },
]

COLUMNS = [
    {
        "entete": "Enseigne",
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
        "entete": "Pays",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "left",
        },
        "width": 14,
    },
    {
        "entete": "CCT",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "left",
        },
        "width": 12,
    },
    {
        "entete": "Nom Client",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "left",
        },
        "width": 25,
    },
    {
        "entete": "Famille Produit",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "left",
        },
        "width": 15,
    },
    {
        "entete": "CA\nCOSIUM\nHT",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "num_format": "#,##0.00",
        },
        "width": 11,
    },
    {
        "entete": "VENTES\nHERON\nHT",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "num_format": "#,##0.00",
        },
        "width": 11,
    },
    {
        "entete": "Taux\nAchats",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "num_format": "#,##0.00%",
        },
        "width": 11,
    },
    {
        "entete": "CA\nCOSIUM\nHT",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "num_format": "#,##0.00",
        },
        "width": 11,
    },
    {
        "entete": "VENTES\nHERON\nHT",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "num_format": "#,##0.00",
        },
        "width": 11,
    },
    {
        "entete": "Taux\nAchats",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "num_format": "#,##0.00%",
        },
        "width": 11,
    },
    {
        "entete": "CA\nCOSIUM\nHT",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "num_format": "#,##0.00",
        },
        "width": 11,
    },
    {
        "entete": "VENTES\nHERON\nHT",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "num_format": "#,##0.00",
        },
        "width": 11,
    },
    {
        "entete": "Taux\nAchats",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "num_format": "#,##0.00%",
        },
        "width": 11,
    },
    {
        "entete": "CA\nCOSIUM\nHT",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "num_format": "#,##0.00",
        },
        "width": 11,
    },
    {
        "entete": "VENTES\nHERON\nHT",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "num_format": "#,##0.00",
        },
        "width": 11,
    },
    {
        "entete": "Taux\nAchats",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "num_format": "#,##0.00%",
        },
        "width": 11,
    },
    {
        "entete": "Commentaire",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
        },
        "width": 50,
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


def excel_familly_ca_cct(file_io: io.BytesIO, file_name: str, client: str) -> dict:
    """Fonction de 5.3A - Contrôle CA Cosium / Ventes Héron par familles."""
    file_path = Path(f"{settings.APPS_DIR!s}/validation_purchases/sql_files/sql_ca_familly_cct.sql")

    def rows():
        # La requête ne renvoie pas la colonne "Commentaire" (dernière colonne de COLUMNS) : on la
        # complète, sinon l'écriture reçoit autant de formats que de valeurs + 1 et échoue
        return [(*row_sql, "") for row_sql in get_rows(file_path, {"client": client})]

    return excel_list_export(
        file_io,
        file_name,
        sheet_name="CA CCT PAR FAMILLES",
        title="5.3A - Contrôle CA Cosium / Ventes Héron par familles",
        columns=COLUMNS,
        rows=rows,
        header_row=4,
        repeat_row=(0, 3),
        in_memory=True,
        merged_headers=merged_month_headers(titres_mois(COLUMNS_TITRES)),
    )
