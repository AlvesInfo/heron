# pylint: disable=W0702,W1203,E1101
"""Module d'export du fichier excel pour les Functions

Commentaire:

created at: 2023-02-23
created by: Paulo ALVES

modified at: 2023-02-23
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
)
from apps.parameters.models import InvoiceFunctions
from apps.parameters.excel_outputs.output_excel_filles_columns import columns_list_functions


def get_row():
    """Class qui renvoie les bonnes colonnes pour le fichier Excel"""

    yield from [
        (
            row.get("function_name"),
            row.get("function"),
            row.get("absolute_path_windows") or "",
            row.get("absolute_path_linux") or "",
            row.get("description") or "",
        )
        for row in InvoiceFunctions.objects.all()
        .values(
            "function_name",
            "function",
            "absolute_path_windows",
            "absolute_path_linux",
            "description",
        )
        .order_by("function_name")
    ]


def excel_liste_functions(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier de liste des Functions"""
    titre_list = file_name.split("_")
    titre = " ".join(titre_list[:-4])
    list_excel = [file_io, [titre[:30]]]
    excel = GenericExcel(list_excel)
    columns = columns_list_functions

    try:
        titre_page_writer(excel, 1, 0, 0, columns, titre)
        output_day_writer(excel, 1, 1, 0)
        columns_headers_writer(excel, 1, 3, 0, columns)
        f_lignes = [dict_row.get("f_ligne") for dict_row in columns]
        f_lignes_odd = [
            {**dict_row.get("f_ligne"), **{"bg_color": "#D9D9D9"}} for dict_row in columns
        ]
        rows_writer(excel, 1, 4, 0, get_row(), f_lignes, f_lignes_odd)
        sheet_formatting(
            excel, 1, columns, {"sens": "landscape", "repeat_row": (0, 5), "fit_page": (1, 0)}
        )

    except:
        LOGGER_EXPORT_EXCEL.exception(f"{file_name!r}")
        return {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}

    finally:
        excel.excel_close()

    return {"OK": f"GENERATION DU FICHIER {file_name} TERMINEE AVEC SUCCES"}