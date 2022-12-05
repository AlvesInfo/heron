# pylint: disable=W0702,W1203
"""Module d'export du fichier excel pour le répertoire des sociétés

Commentaire:

created at: 2022-05-12
created by: Paulo ALVES

modified at: 2022-05-12
modified by: Paulo ALVES
"""
import io
from typing import Dict

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
from apps.book.models import Society, SupplierCct

COLUMNS = [
    {
        "entete": "CCT X3",
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
        "entete": "Maison",
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
        "width": 34,
    },
    {
        "entete": "Identifiants",
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
        "width": 101,
    }
]


def get_rows(parmas_dict: Dict):
    """Renvoie les résultats de la requête nécessaire à l'export excel
    :param parmas_dict: paramètre de la requête
    :return: resultats de la requête
    """

    return [
        (
            row.axe_cct.cct,
            row.axe_cct.name,
            row.cct_identifier
        )
        for row in SupplierCct.objects.filter(**parmas_dict).order_by("axe_cct")
    ]


def excel_liste_supplier_cct(file_io: io.BytesIO, file_name: str, parmas_dict: dict) -> dict:
    """Fonction de génération du fichier de liste des identificant pour les cct, pour un tiers X3"""
    supplier = Society.objects.get(**parmas_dict)
    titre = f"Identificants pour les CCT : {str(supplier)}"
    list_excel = [file_io, [parmas_dict.get("third_party_num")]]
    excel = GenericExcel(list_excel)
    get_clean_rows = get_rows(parmas_dict)

    try:
        titre_page_writer(excel, 1, 0, 0, COLUMNS, titre)
        output_day_writer(excel, 1, 1, 0)
        columns_headers_writer(excel, 1, 3, 0, COLUMNS)
        f_lignes = [dict_row.get("f_ligne") for dict_row in COLUMNS]
        f_lignes_odd = [
            {**dict_row.get("f_ligne"), **{"bg_color": "#E0E0E0"}} for dict_row in COLUMNS
        ]
        rows_writer(excel, 1, 4, 0, get_clean_rows, f_lignes, f_lignes_odd)
        sheet_formatting(
            excel, 1, COLUMNS, {"sens": "portrait", "repeat_row": (0, 5), "fit_page": (1, 0)}
        )

    except:
        LOGGER_EXPORT_EXCEL.exception(f"{file_name!r}")
        return {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}

    finally:
        excel.excel_close()

    return {"OK": f"GENERATION DU FICHIER {file_name} TERMINEE AVEC SUCCES"}
