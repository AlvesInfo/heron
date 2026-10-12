"""Module d'export du fichier excel pour les factures du tiers pas mois

Commentaire:

created at: 2022-05-12
created by: Paulo ALVES

modified at: 2022-05-12
modified by: Paulo ALVES
"""
import io
from pathlib import Path

import pendulum
from django.db import connection
from django.conf import settings
from apps.core.excel_outputs.excel_writer import (
    f_entetes,
    f_ligne,
)
from apps.core.excel_outputs.generic_list_export import excel_list_export, month_headers

COLUMNS_TITRES = [
    {
        "entete": "M",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
    },
    {
        "entete": "M1",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
    },
    {
        "entete": "TRIMESTRE GLISSANT",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
    },
    {
        "entete": "12 MOIS GLISSANTS",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
    },
]

COLUMNS = [
    {
        "entete": "Enseigne",
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
        "entete": "Pays",
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
        "width": 14,
    },
    {
        "entete": "CCT",
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
        "width": 12,
    },
    {
        "entete": "Nom Client",
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
        "width": 25,
    },
    {
        "entete": "CA\nCOSIUM\nHT",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "num_format": "#,##0.00",
            },
        },
        "width": 11,
    },
    {
        "entete": "VENTES\nHERON\nHT",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "num_format": "#,##0.00",
            },
        },
        "width": 11,
    },
    {
        "entete": "Taux\nAchats",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "num_format": "#,##0.00%",
            },
        },
        "width": 11,
    },
    {
        "entete": "CA\nCOSIUM\nHT",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "num_format": "#,##0.00",
            },
        },
        "width": 11,
    },
    {
        "entete": "VENTES\nHERON\nHT",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "num_format": "#,##0.00",
            },
        },
        "width": 11,
    },
    {
        "entete": "Taux\nAchats",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "num_format": "#,##0.00%",
            },
        },
        "width": 11,
    },
    {
        "entete": "CA\nCOSIUM\nHT",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "num_format": "#,##0.00",
            },
        },
        "width": 11,
    },
    {
        "entete": "VENTES\nHERON\nHT",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "num_format": "#,##0.00",
            },
        },
        "width": 11,
    },
    {
        "entete": "Taux\nAchats",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "num_format": "#,##0.00%",
            },
        },
        "width": 11,
    },
    {
        "entete": "CA\nCOSIUM\nHT",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "num_format": "#,##0.00",
            },
        },
        "width": 11,
    },
    {
        "entete": "VENTES\nHERON\nHT",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "num_format": "#,##0.00",
            },
        },
        "width": 11,
    },
    {
        "entete": "Taux\nAchats",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "num_format": "#,##0.00%",
            },
        },
        "width": 11,
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
            **{},
        },
        "width": 50,
    },
]


def get_rows(file_path: Path, parmas_dict: dict = None):
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


def titres_mois(columns_titres: list[dict]) -> list[dict]:
    """Les deux premiers titres fusionnés reçoivent les mois M-1 et M-2 en majuscules"""
    months = [
        pendulum.now().subtract(months=mois).start_of("month").format("MMMM YYYY", locale="fr").upper()
        for mois in (1, 2)
    ]
    return month_headers(columns_titres, (0, 1), months)


def merged_month_headers(columns_titres: list[dict], first_col: int = 4, width: int = 3) -> list[tuple]:
    """Entêtes fusionnées de `width` colonnes à partir de first_col, une par titre"""
    return [
        (first_col + width * i, first_col + width * i + width - 1, titre["entete"], titre["f_entete"])
        for i, titre in enumerate(columns_titres)
    ]


def excel_ca_cct(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de 5.3 - Contrôle CA Cosium / Ventes Héron"""
    file_path = Path(f"{settings.APPS_DIR!s}/validation_purchases/sql_files/sql_ca_cct.sql")

    return excel_list_export(
        file_io,
        file_name,
        sheet_name="CA CCT",
        title="5.3 - Contrôle CA Cosium / Ventes Héron",
        columns=COLUMNS,
        rows=lambda: get_rows(file_path),
        header_row=4,
        repeat_row=(0, 3),
        in_memory=True,
        merged_headers=merged_month_headers(titres_mois(COLUMNS_TITRES)),
    )
