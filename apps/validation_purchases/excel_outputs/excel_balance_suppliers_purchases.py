"""Module d'export du fichier excel pour les factures du tiers pas mois.

Commentaire:

created at: 2022-05-12
created by: Paulo ALVES

modified at: 2022-05-12
modified by: Paulo ALVES
"""

import io
from pathlib import Path

import pendulum
from django.conf import settings
from django.db import connection
from django.db.models import Q

from apps.core.excel_outputs.excel_writer import (
    f_entetes,
    f_ligne,
)
from apps.core.excel_outputs.generic_list_export import excel_list_export, month_headers
from apps.edi.models import EdiValidation

COLUMNS_CLIENT = [
    {
        "entete": "CCT",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "left",
            "bold": True,
        },
        "width": 51,
    },
    {
        "entete": "Enseigne",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "center",
            "bold": True,
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
            "bold": True,
        },
        "width": 14,
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
            "bold": True,
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
            "bold": True,
        },
        "width": 10,
    },
]

COLUMNS = [
    {
        "entete": "Tiers",
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
        "entete": "Nom du tiers",
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


def validation_start_date():
    """Début de la période de validation ouverte, sinon le mois courant."""
    validation = EdiValidation.objects.filter(Q(final=False) | Q(final__isnull=True)).first()
    return pendulum.parse(validation.billing_period.isoformat()) if validation else pendulum.now()


def columns_mois() -> list[dict]:
    """Colonnes 2 à 5 : les quatre mois précédant la période de validation."""
    start_date = validation_start_date()
    months = [
        start_date.add(months=mois)
        .start_of("month")
        .format("MMMM YYYY", locale="fr")
        .capitalize()
        .replace(" ", "\n")
        for mois in (-3, -2, -1, 0)
    ]
    return month_headers(COLUMNS, (2, 3, 4, 5), months)


def excel_balance_suppliers_purchases(
    file_io: io.BytesIO, file_name: str, params_dict: dict
) -> dict:
    """Fonction de génération du fichier de Contrôle 5.1 Fournisseurs M vs M-1."""
    file_path = Path(
        f"{settings.APPS_DIR!s}/validation_purchases/sql_files/sql_suppliers_invoices_m_m1.sql"
    )

    return excel_list_export(
        file_io,
        file_name,
        sheet_name="FOURNISSEURS",
        title="5.1 Fournisseurs M vs M-1",
        columns=columns_mois,
        rows=lambda: get_rows(file_path, params_dict),
        repeat_row=(0, 3),
        in_memory=True,
    )
