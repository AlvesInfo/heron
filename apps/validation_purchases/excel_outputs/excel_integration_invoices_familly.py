"""Module d'export du fichier excel pour les facturs founisseurs intégrées sans CCT.

Commentaire:

created at: 2022-05-12
created by: Paulo ALVES

modified at: 2022-05-12
modified by: Paulo ALVES
"""

import io

import pendulum
from django.db import connection

from apps.core.excel_outputs.excel_writer import (
    f_entetes,
    f_ligne,
)
from apps.core.excel_outputs.generic_list_export import excel_list_export, month_headers
from apps.core.functions.functions_postgresql import query_file_cursor

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
        "width": 10,
    },
    {
        "entete": "Fournisseur",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
        },
        "width": 32,
    },
    {
        "entete": "Axe Pro",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {**f_ligne, "align": "center"},
        "width": 18,
    },
    {
        "entete": "Mois-2\n",
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
        "entete": "Mois-1\n",
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
        "entete": "Mois M\n",
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
        "entete": "Variation",
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
        "entete": "Commentaire",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "text_wrap": True,
        },
        "width": 80,
    },
]


def get_rows(cursor):
    """Renvoie les résultats de la requête nécessaire à l'export excel.

    :return: resultats de la requête.
    """
    sql_context_file = "apps/validation_purchases/sql_files/sql_families_invoices.sql"
    return query_file_cursor(cursor, file_path=sql_context_file)


def columns_mois() -> list[dict]:
    """Colonnes dont les entêtes 3 à 5 portent les mois M-2, M-1 et M."""
    mois = pendulum.now().start_of("month")
    libelles = [
        f"Mois-2\n{mois.subtract(months=3).format('MMM YYYY', locale='fr')}",
        f"Mois-1\n{mois.subtract(months=2).format('MMM YYYY', locale='fr')}",
        f"Mois M\n{mois.subtract(months=1).format('MMM YYYY', locale='fr')}",
    ]
    return month_headers(COLUMNS, (3, 4, 5), libelles)


def rows_familles() -> list[tuple]:
    """Lignes des familles facturées, limitées aux 8 colonnes du tableau."""
    with connection.cursor() as cursor:
        return [rows[:8] for rows in get_rows(cursor)]


def excel_integration_invoices_familly(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier Excel de la liste des factures intégrées sans CCT."""
    titre = " ".join(file_name.split("_")[:-3])

    return excel_list_export(
        file_io,
        file_name,
        sheet_name=titre,
        title=titre,
        columns=columns_mois,
        rows=rows_familles,
        orientation="landscape",
    )
