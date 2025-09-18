# pylint: disable=W0702,W1203
"""Module d'export du fichier de la liste des couples Tiers / Masions à exlucre de la facturation

Commentaire:

created at: 2023-01-21
created by: Paulo ALVES

modified at: 2023-01-21
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
from apps.centers_clients.models import MaisonSupllierExclusion

columns = [
    {
        "entete": "TIERS X3",
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
        "width": 50,
    },
    {
        "entete": "CLIENT",
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
        "width": 50,
    },
]


def get_clean_rows():
    """Retourne les lignes à écrire"""

    return [
        (str(row.third_party_num), str(row.maison)) for row in MaisonSupllierExclusion.objects.all()
    ]


def excel_liste_exclusion(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier de liste exclusions Tiers X3/Clients"""
    list_excel = [file_io, ["LISTE DES EXCLUSIONS"]]
    excel = GenericExcel(list_excel)

    try:
        titre_page_writer(excel, 1, 0, 0, columns, "LISTE DES EXCLUSIONS TIERS X3/CLIENTS")
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
