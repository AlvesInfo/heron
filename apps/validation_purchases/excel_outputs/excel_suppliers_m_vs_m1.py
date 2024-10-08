# pylint: disable=E0401,W0702,W1203,R0914,W1309
"""Module d'export du fichier excel pour les factures du tiers pas mois

Commentaire:

created at: 2022-05-12
created by: Paulo ALVES

modified at: 2022-05-12
modified by: Paulo ALVES
"""
import io
from typing import Dict, AnyStr
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


def excel_suppliers_m_vs_m1(file_io: io.BytesIO, file_name: AnyStr, client: AnyStr) -> dict:
    """Fonction de génération du fichier de Contrôle Fournisseurs M vs M-1"""
    titre = f"5.A - Contrôle Fournisseurs M vs M-1"
    list_excel = [file_io, ["CCT FOURNISSEURS"]]
    excel = GenericExcel(list_excel)
    file_path = Path(f"{str(APPS_DIR)}/validation_purchases/sql_files/sql_suppliers_m_vs_m1.sql")

    get_clean_rows = [row[:-2] for row in get_rows(file_path, {"client": client})]
    if get_clean_rows:
        client_attrs_list = [get_clean_rows[0][:5]]
    else:
        client_attrs_list = [
            (
                None,
                None,
                None,
                None,
                None,
            ),
        ]
    get_list_rows = [row[5:] for row in get_clean_rows]
    mois = 4

    for i, column_dict in enumerate(COLUMNS, 1):
        if 1 < i < 6:
            column_dict["entete"] = (
                (
                    pendulum.now()
                    .subtract(months=mois)
                    .start_of("month")
                    .format("MMMM YYYY", locale="fr")
                )
                .capitalize()
                .replace(" ", "\n")
            )
            mois -= 1

    try:
        titre_page_writer(excel, 1, 0, 0, COLUMNS, titre)
        output_day_writer(excel, 1, 1, 0)
        f_clients = [dict_row.get("f_ligne") for dict_row in COLUMNS_CLIENT]
        f_lignes = [dict_row.get("f_ligne") for dict_row in COLUMNS]
        f_lignes_odd = [
            {**dict_row.get("f_ligne"), **{"bg_color": "#D9D9D9"}} for dict_row in COLUMNS
        ]

        # MISE EN PLACE DES DONNEES DU CLIENT CCT
        columns_headers_writer(excel, 1, 3, 0, COLUMNS_CLIENT)
        rows_writer(excel, 1, 4, 0, client_attrs_list, f_clients, f_clients)

        # MISE EN PLACE DES LIGNES DES FOURNISSEURS
        columns_headers_writer(excel, 1, 6, 0, COLUMNS)
        rows_writer(excel, 1, 7, 0, get_list_rows, f_lignes, f_lignes_odd)
        sheet_formatting(
            excel, 1, COLUMNS, {"sens": "portrait", "repeat_row": (0, 3), "fit_page": (1, 0)}
        )

    except:
        LOGGER_EXPORT_EXCEL.exception(f"{file_name!r}")
        return {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}

    finally:
        excel.excel_close()

    return {"OK": f"GENERATION DU FICHIER {file_name} TERMINEE AVEC SUCCES"}
