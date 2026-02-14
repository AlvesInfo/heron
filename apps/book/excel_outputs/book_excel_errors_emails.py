# pylint: disable=W0702,W1203
"""Module d'export du fichier excel pour le répertoire des sociétés

Commentaire:

created at: 2022-05-12
created by: Paulo ALVES

modified at: 2022-05-12
modified by: Paulo ALVES
"""

import io

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
from apps.book.bin.checks import check_emails

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
        "entete": "Email en erreur",
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
        "width": 50,
    },
]


def get_rows():
    """Renvoie les résultats de la requête nécessaire à l'export excel
    :return: resultats de la requête
    """
    return [
        (emails_dict["third_party_num"], emails_dict["email"])
        for emails_dict in check_emails()
    ]


def excel_errors_emails(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier de liste des identificant pour les cct, pour un tiers X3"""
    titre = "Emails tiers en erreur dans Sage X3 (Tiers)"
    list_excel = [file_io, ["Emails"]]
    excel = GenericExcel(list_excel)
    get_clean_rows = get_rows()

    try:
        titre_page_writer(excel, 1, 0, 0, COLUMNS, titre)
        output_day_writer(excel, 1, 1, 0)
        columns_headers_writer(excel, 1, 3, 0, COLUMNS)
        f_lignes = [dict_row.get("f_ligne") for dict_row in COLUMNS]
        f_lignes_odd = [
            {**dict_row.get("f_ligne"), **{"bg_color": "#E0E0E0"}}
            for dict_row in COLUMNS
        ]
        rows_writer(excel, 1, 4, 0, get_clean_rows, f_lignes, f_lignes_odd)
        sheet_formatting(
            excel,
            1,
            COLUMNS,
            {"sens": "portrait", "repeat_row": (0, 5), "fit_page": (1, 0)},
        )

    except Exception as error:
        LOGGER_EXPORT_EXCEL.exception(f"{file_name!r} : {error!r}")
        return {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}

    finally:
        excel.excel_close()

    return {"OK": f"GENERATION DU FICHIER {file_name} TERMINEE AVEC SUCCES"}
