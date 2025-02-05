# pylint: disable=W0702,W1203
"""Module d'export des Abonnement par maisons

Commentaire:

created at: 2023-03-01
created by: Paulo ALVES

modified at: 2023-03-01
modified by: Paulo ALVES
"""

import io

from heron.loggers import LOGGER_EXPORT_EXCEL
from apps.core.functions.functions_excel import GenericExcel
from apps.core.excel_outputs.excel_writer import (
    titre_page_writer,
    output_day_writer,
    columns_headers_writer,
    sheet_formatting,
    rows_writer,
    f_entetes,
    f_ligne,
)
from apps.centers_clients.models import MaisonSubcription

columns = [
    {
        "entete": "CODE MAISON",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{"align": "center"},
        },
        "width": 9,
    },
    {
        "entete": "MAISON",
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
        "width": 40,
    },
    {
        "entete": "ARTICLE",
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
        "width": 25,
    },
    {
        "entete": "QTY",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "num_format": "#,##0",
            },
        },
        "width": 8,
    },
    {
        "entete": "UNITE",
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
        "width": 7,
    },
    {
        "entete": "PRIX NET",
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
        "width": 9,
    },
    {
        "entete": "FONCTION",
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
        "width": 12,
    },
    {
        "entete": "ENSEIGNE",
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
        "width": 12,
    },
]


def get_clean_rows():
    """Retourne les lignes à écrire"""

    return [
        (
            row_dict.get("maison", ""),
            row_dict.get("maison__intitule", ""),
            row_dict.get("article__reference", ""),
            row_dict.get("qty", ""),
            row_dict.get("unit_weight__unity", ""),
            row_dict.get("net_unit_price", ""),
            row_dict.get("function", ""),
            row_dict.get("for_signboard", ""),
        )
        for row_dict in MaisonSubcription.objects.all().values(
            "maison",
            "maison__intitule",
            "article__reference",
            "qty",
            "unit_weight__unity",
            "net_unit_price",
            "function",
            "for_signboard",
        )
    ]


def excel_liste_subscriptions(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier de la liste des Abonnements par maisons"""
    list_excel = [file_io, ["LISTE DES ABONNEMENTS"]]
    excel = GenericExcel(list_excel)

    try:
        titre_page_writer(excel, 1, 0, 0, columns, "LISTE DES ABONNEMENTS / CLIENTS")
        output_day_writer(excel, 1, 1, 0)
        columns_headers_writer(excel, 1, 3, 0, columns)
        f_lignes = [dict_row.get("f_ligne") for dict_row in columns]
        f_lignes_odd = [
            {**dict_row.get("f_ligne"), **{"bg_color": "#D9D9D9"}} for dict_row in columns
        ]
        rows_writer(excel, 1, 4, 0, get_clean_rows(), f_lignes, f_lignes_odd)
        sheet_formatting(
            excel, 1, columns, {"sens": "portrait", "repeat_row": (0, 5), "fit_page": (1, 0)}
        )

    except:
        LOGGER_EXPORT_EXCEL.exception(f"{file_name!r}")
        return {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}

    finally:
        excel.excel_close()

    return {"OK": f"GENERATION DU FICHIER {file_name} TERMINEE AVEC SUCCES"}
