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
from apps.core.excel_outputs.generic_list_export import excel_list_export, month_headers
from apps.validation_purchases.excel_outputs.excel_balance_suppliers_purchases import (
    validation_start_date,
)

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
        "width": 51,
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
        "width": 10,
    },
    {
        "entete": "Date\nOuverture",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "center",
            "num_format": "dd/mm/yy",
        },
        "width": 10,
    },
    {
        "entete": "Date\nFermeture",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "center",
            "num_format": "dd/mm/yy",
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
        "width": 11,
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
        "width": 11,
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
        "width": 11,
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
        "width": 11,
    },
    {
        "entete": "Variation\nM vs M-1",
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


def columns_mois() -> list[dict]:
    """Colonnes 6 à 9 : les quatre mois précédant la période de validation."""
    start_date = validation_start_date()
    months = [
        start_date.add(months=mois)
        .start_of("month")
        .format("MMMM YYYY", locale="fr")
        .capitalize()
        .replace(" ", "\n")
        for mois in (-3, -2, -1, 0)
    ]
    return month_headers(COLUMNS, (6, 7, 8, 9), months)


def red_conditional_formats(excel, sheet: int, first_row: int, nb_rows: int) -> None:
    """Cellules en rouge si la maison est fermée (F) et facturée (J), ou si elle est en BLOCAGE (D).

    et facturée : lignes Excel first_row + 1 à first_row + nb_rows.
    """
    style = {"font_color": "#FFFFFF", "bg_color": "red", "bold": True}

    for i in range(first_row + 1, first_row + 1 + nb_rows):
        closed = f'=IF(J{i}=0,False,IF(F{i}="",False,True))'
        blocked = f'=IF(J{i}=0,False,IF(D{i}="BLOCAGE",True,False))'

        for plage, criteria in (
            ("F", closed),
            ("J", closed),
            ("A", blocked),
            ("B", blocked),
            ("C", blocked),
            ("D", blocked),
            ("J", blocked),
        ):
            excel.conditional_value(
                num_sheet=sheet,
                str_plage=f"{plage}{i}",
                valeur=0,
                type_format="formula",
                criteria=criteria,
                style=style,
            )


def excel_refac_cct(file_io: io.BytesIO, file_name: str, params_dict: dict) -> dict:
    """Fonction de génération du fichier de liste des Tiers, Fournisseurs, Clients."""
    file_path = Path(f"{settings.APPS_DIR!s}/validation_purchases/sql_files/sql_refac_cct.sql")

    return excel_list_export(
        file_io,
        file_name,
        sheet_name="REFAC PAR CCT",
        title="5.0 - Contrôle Refac M M-1 par CCT",
        columns=columns_mois,
        rows=lambda: [row[:-1] for row in get_rows(file_path, params_dict)],
        repeat_row=(0, 3),
        in_memory=True,
        after_rows=red_conditional_formats,
    )
