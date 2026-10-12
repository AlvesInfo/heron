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
        "entete": "tiers X3",
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
        "entete": "Type",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "center",
        },
        "width": 9,
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
        "width": 20,
    },
    {
        "entete": "Mois facture",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "center",
            "num_format": "mmmm yyyy",
        },
        "width": 12,
    },
    {
        "entete": "factures",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "left",
            "text_wrap": True,
        },
        "width": 80,
    },
    {
        "entete": "Référence Article",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "center",
        },
        "width": 20,
    },
    {
        "entete": "Axe RFA",
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
        return [row[1:9] for row in cursor.fetchall()]


def control_rfa_period_excel(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier de l'étape 3.6 - Contrôle période RFA."""
    titre = "3.6 - Contrôle période RFA"
    file_path = Path(
        f"{settings.APPS_DIR!s}/validation_purchases/sql_files/sql_control_rfa_period.sql"
    )
    get_clean_rows = [row[:-1] for row in get_rows(file_path)]

    return excel_list_export(
        file_io,
        file_name,
        sheet_name="RFA",
        title=titre,
        columns=COLUMNS,
        rows=get_clean_rows,
        orientation="landscape",
        repeat_row=(0, 3),
        in_memory=True,
    )
