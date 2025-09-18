# pylint: disable=E0401,W0702,W1203
"""Module d'export du fichier excel pour les facturs founisseurs intégrées sans CCT

Commentaire:

created at: 2022-05-12
created by: Paulo ALVES

modified at: 2022-05-12
modified by: Paulo ALVES
"""
import io

import pendulum
from django.db import connection

from heron.loggers import LOGGER_EXPORT_EXCEL
from apps.core.functions.functions_postgresql import query_file_cursor
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

COLUMNS = [
    {
        "entete": "Tiers X3",
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
        "width": 10,
    },
    {
        "entete": "Fournisseur",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
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
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {**f_ligne, **{"align": "center"}},
        "width": 18,
    },
    {
        "entete": "Mois-2\n",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{"num_format": "#,##0.00"},
        },
        "width": 11,
    },
    {
        "entete": "Mois-1\n",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{"num_format": "#,##0.00"},
        },
        "width": 11,
    },
    {
        "entete": "Mois M\n",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{"num_format": "#,##0.00"},
        },
        "width": 11,
    },
    {
        "entete": "Variation",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{"num_format": "#,##0.00"},
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
            **{
                "text_wrap": True,
            },
        },
        "width": 80,
    },
]


def get_rows(cursor):
    """Renvoie les résultats de la requête nécessaire à l'export excel
    :return: resultats de la requête
    """
    sql_context_file = "apps/validation_purchases/sql_files/sql_families_invoices.sql"
    invoices_famillies = query_file_cursor(cursor, file_path=sql_context_file)
    return invoices_famillies


def excel_integration_invoices_familly(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier Excel de la liste des factures intégrées sans CCT"""
    titre_list = file_name.split("_")
    titre = " ".join(titre_list[:-3])
    list_excel = [file_io, [titre]]
    excel = GenericExcel(list_excel)

    try:
        with connection.cursor() as cursor:
            mois = pendulum.now().start_of("month")
            mois_m = mois.subtract(months=1).format("MMM YYYY", locale="fr")
            mois_1 = mois.subtract(months=2).format("MMM YYYY", locale="fr")
            mois_2 = mois.subtract(months=3).format("MMM YYYY", locale="fr")

            for i, column in enumerate(COLUMNS):
                if i == 3:
                    column["entete"] = f"Mois-2\n{mois_2}"
                if i == 4:
                    column["entete"] = f"Mois-1\n{mois_1}"
                if i == 5:
                    column["entete"] = f"Mois M\n{mois_m}"

            titre_page_writer(excel, 1, 0, 0, COLUMNS, titre)
            output_day_writer(excel, 1, 1, 0)
            columns_headers_writer(excel, 1, 3, 0, COLUMNS)
            f_lignes = [dict_row.get("f_ligne") for dict_row in COLUMNS]
            f_lignes_odd = [
                {**dict_row.get("f_ligne"), **{"bg_color": "#D9D9D9"}}
                for i, dict_row in enumerate(COLUMNS)
            ]
            rows_writer(
                excel, 1, 4, 0, [rows[:8] for rows in get_rows(cursor)], f_lignes, f_lignes_odd
            )
            sheet_formatting(
                excel, 1, COLUMNS, {"sens": "landscape", "repeat_row": (0, 5), "fit_page": (1, 0)}
            )

    except:
        LOGGER_EXPORT_EXCEL.exception(f"{file_name!r}")
        return {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}

    finally:
        excel.excel_close()

    return {"OK": f"GENERATION DU FICHIER {file_name} TERMINEE AVEC SUCCES"}
