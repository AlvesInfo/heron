"""Module d'export du fichier excel du Contrôle des achats.

des CCT franchiseur (CAHA, MARK, INFO, etc…).

Commentaire:

created at: 2023-07-03
created by: Paulo ALVES

modified at: 2023-07-03
modified by: Paulo ALVES
"""

import io
from pathlib import Path

import pendulum
from django.conf import settings
from django.db import connection

from apps.core.excel_outputs.excel_writer import (
    columns_headers_writer,
    f_entetes,
    f_ligne,
)
from apps.core.excel_outputs.generic_list_export import (
    PAGE_NUMBERS_FOOTER,
    excel_list_export,
    month_headers,
)

COLUMNS = [
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
        "width": 51,
    },
    {
        "entete": "M-11",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "num_format": "#,##0.00",
        },
        "width": 10,
    },
    {
        "entete": "M-10",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "num_format": "#,##0.00",
        },
        "width": 10,
    },
    {
        "entete": "M-9",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "num_format": "#,##0.00",
        },
        "width": 10,
    },
    {
        "entete": "M-8",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "num_format": "#,##0.00",
        },
        "width": 10,
    },
    {
        "entete": "M-7",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "num_format": "#,##0.00",
        },
        "width": 10,
    },
    {
        "entete": "M-6",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "num_format": "#,##0.00",
        },
        "width": 10,
    },
    {
        "entete": "M-5",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "num_format": "#,##0.00",
        },
        "width": 10,
    },
    {
        "entete": "M-4",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "num_format": "#,##0.00",
        },
        "width": 10,
    },
    {
        "entete": "M-3",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "num_format": "#,##0.00",
        },
        "width": 10,
    },
    {
        "entete": "M-2",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "num_format": "#,##0.00",
        },
        "width": 10,
    },
    {
        "entete": "M-1",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "num_format": "#,##0.00",
        },
        "width": 10,
    },
    {
        "entete": "M",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "num_format": "#,##0.00",
        },
        "width": 10,
    },
    {
        "entete": "Total des 6\nderniers mois",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "num_format": "#,##0.00",
        },
        "width": 14,
    },
    {
        "entete": "Commentaires",
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


FORMAT_CLIENT = {
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


def columns_mois() -> list[dict]:
    """Colonnes dont les entêtes portent les mois, calculées à chaque export."""
    months = [
        pendulum.now()
        .subtract(months=mois)
        .start_of("month")
        .format("MMMM YYYY", locale="fr")
        .capitalize()
        .replace(" ", "\n")
        for mois in range(12, 0, -1)
    ]
    return month_headers(COLUMNS, range(1, 13), months)


def write_rows(
    excel, sheet: int, columns: list, rows, f_lignes: list, f_lignes_odd: list
) -> list[int]:
    """Un bloc par client : nom, entêtes, lignes ; renvoie les sauts de page entre les blocs."""
    row, row_format, current_client, page_breaks = 2, 1, "", []

    for client, *line in rows:
        if current_client != client:
            row += 1

            if row > 5:
                page_breaks.append(row)

            excel.write_row(sheet, row, 0, client, FORMAT_CLIENT)
            row += 1
            columns_headers_writer(excel, sheet, row, 0, columns)
            current_client, row, row_format = client, row + 1, 1

        excel.write_rows(sheet, row, 0, line, f_lignes if row_format % 2 == 0 else f_lignes_odd)
        row += 1
        row_format += 1

    return page_breaks


def excel_cct_franchiseurs(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier de liste des Tiers, Fournisseurs, Clients."""
    file_path = Path(
        f"{settings.APPS_DIR!s}/validation_purchases/sql_files/sql_cct_franchiseur.sql"
    )

    return excel_list_export(
        file_io,
        file_name,
        sheet_name="CCT - FRANCHISEURS",
        title="3.2 - Contrôle des CCT/franchiseurs (MARK, INFO, etc…)",
        columns=columns_mois,
        rows=lambda: get_rows(file_path),
        orientation="landscape",
        repeat_row=(0, 2),
        write_headers=False,
        writer=write_rows,
        footer=PAGE_NUMBERS_FOOTER,
    )
