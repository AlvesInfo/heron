"""Module d'export du fichier excel pour les factures du tiers pas mois

Commentaire:

created at: 2022-05-12
created by: Paulo ALVES

modified at: 2022-05-12
modified by: Paulo ALVES
"""
import io
from typing import AnyStr
from pathlib import Path

import pendulum
from django.db import connection
from django.conf import settings
from apps.core.excel_outputs.excel_writer import (
    f_entetes,
    f_ligne,
    columns_headers_writer,
)
from apps.core.excel_outputs.generic_list_export import excel_list_export, month_headers, write_alternate_rows

COLUMNS_CLIENT = [
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
                "bold": True,
            },
        },
        "width": 51,
    },
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
                "bold": True,
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
                "bold": True,
            },
        },
        "width": 14,
    },
    {
        "entete": "Date\nOuverture",
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
                "num_format": "dd/mm/yy",
                "bold": True,
            },
        },
        "width": 10,
    },
    {
        "entete": "Date\nFermeture",
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
                "num_format": "dd/mm/yy",
                "bold": True,
            },
        },
        "width": 10,
    },
]

COLUMNS = [
    {
        "entete": "Tiers",
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
        "width": 51,
    },
    {
        "entete": "M-3",
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
        "width": 10,
    },
    {
        "entete": "M-2",
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
        "width": 10,
    },
    {
        "entete": "M-1",
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
        "width": 10,
    },
    {
        "entete": "M",
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
        "width": 10,
    },
    {
        "entete": "Variation\nM vs M-1",
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
        "width": 14,
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


def columns_mois() -> list[dict]:
    """Colonnes 1 à 4 : les mois M-4 à M-1"""
    months = [
        pendulum.now().subtract(months=mois).start_of("month").format("MMMM YYYY", locale="fr").capitalize().replace(" ", "\n")
        for mois in (4, 3, 2, 1)
    ]
    return month_headers(COLUMNS, (1, 2, 3, 4), months)


def write_client_and_suppliers(excel, sheet: int, columns: list, rows: list, f_lignes: list, f_lignes_odd: list) -> None:
    """Bloc du client cct (entêtes ligne 3, valeurs ligne 4) puis tableau des fournisseurs (ligne 6)"""
    client_attrs_list = [rows[0][:5]] if rows else [(None, None, None, None, None)]
    f_clients = [dict_row.get("f_ligne") for dict_row in COLUMNS_CLIENT]
    columns_headers_writer(excel, sheet, 3, 0, COLUMNS_CLIENT)
    write_alternate_rows(excel, sheet, 4, client_attrs_list, f_clients, f_clients)
    columns_headers_writer(excel, sheet, 6, 0, columns)
    write_alternate_rows(excel, sheet, 7, [row[5:] for row in rows], f_lignes, f_lignes_odd)


def excel_suppliers_m_vs_m1(file_io: io.BytesIO, file_name: AnyStr, client: AnyStr) -> dict:
    """Fonction de génération du fichier de Contrôle Fournisseurs M vs M-1"""
    file_path = Path(f"{settings.APPS_DIR!s}/validation_purchases/sql_files/sql_suppliers_m_vs_m1.sql")

    return excel_list_export(
        file_io,
        file_name,
        sheet_name="CCT FOURNISSEURS",
        title="5.A - Contrôle Fournisseurs M vs M-1",
        columns=columns_mois,
        rows=lambda: [row[:-2] for row in get_rows(file_path, {"client": client})],
        repeat_row=(0, 3),
        in_memory=True,
        write_headers=False,
        writer=write_client_and_suppliers,
    )
