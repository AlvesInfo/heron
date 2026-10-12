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

from django.db import connection
from django.conf import settings
from apps.core.excel_outputs.excel_writer import (
    f_entetes,
    f_ligne,
)
from apps.core.excel_outputs.generic_list_export import excel_list_export


COLUMNS = [
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
        "width": 10,
    },
    {
        "entete": "Client",
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
        "width": 20,
    },
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
        "width": 40,
    },
    {
        "entete": "N° Facture",
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
        "width": 15,
    },
    {
        "entete": "Date\nfacture",
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
        "entete": "Mois\nFacture",
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
        "entete": "Montant TTC",
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
        "entete": "Montant HT",
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


def excel_third_suppliers_m_vs_m1(
    file_io: io.BytesIO, file_name: AnyStr, client: AnyStr, third_party_num: AnyStr
) -> dict:
    """Fonction de génération du fichier de Contrôle Details Fournisseurs M vs M-1"""
    file_path = Path(
        f"{settings.APPS_DIR!s}/validation_purchases/sql_files/sql_third_suppliers_m_vs_m1.sql"
    )

    return excel_list_export(
        file_io,
        file_name,
        sheet_name=third_party_num,
        title="5.B - Contrôle Details Fournisseurs M vs M-1",
        columns=COLUMNS,
        rows=lambda: get_rows(file_path, {"client": client, "third_party_num": third_party_num}),
        repeat_row=(0, 3),
        in_memory=True,
    )
