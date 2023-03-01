# pylint: disable=W0702,W1203,E1101
"""Module d'export du fichier excel pour les Catégories

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
    titre_page_writer,
    output_day_writer,
    columns_headers_writer,
    sheet_formatting,
    rows_writer,
)
from apps.parameters.models import Category
from apps.parameters.excel_outputs.output_excel_filles_columns import columns_list_categories


def get_row():
    """Class qui renvoie les bonnes colonnes pour le fichier Excel"""

    yield from [
        (
            row.get("ranking"),
            row.get("code"),
            row.get("name"),
            row.get("big_sub_category__ranking") or "",
            row.get("big_sub_category__code") or "",
            row.get("big_sub_category__name") or "",
        )
        for row in Category.objects.all()
        .order_by("ranking", "big_sub_category__code")
        .values(
            "ranking",
            "code",
            "name",
            "big_sub_category__ranking",
            "big_sub_category__code",
            "big_sub_category__name",
        )
        .order_by("ranking", "big_sub_category__ranking")
    ]


def excel_liste_categories(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier de liste des Catégories"""
    titre_list = file_name.split("_")
    titre = " ".join(titre_list[:-4])
    list_excel = [file_io, [titre[:30]]]
    excel = GenericExcel(list_excel)
    columns = columns_list_categories

    try:
        titre_page_writer(excel, 1, 0, 0, columns, titre)
        output_day_writer(excel, 1, 1, 0)
        excel.write_merge_h(1, 3, 0, 2, "Grande Catégorie", columns[0].get("f_entete"))
        excel.write_merge_h(1, 3, 3, 5, "Rubrique Prestation associée", columns[3].get("f_entete"))
        columns_headers_writer(excel, 1, 4, 0, columns)
        f_lignes = [dict_row.get("f_ligne") for dict_row in columns]
        f_lignes_odd = [
            {**dict_row.get("f_ligne"), **{"bg_color": "#D9D9D9"}} for dict_row in columns
        ]
        rows_writer(excel, 1, 5, 0, get_row(), f_lignes, f_lignes_odd)
        sheet_formatting(
            excel, 1, columns, {"sens": "portrait", "repeat_row": (0, 5), "fit_page": (1, 0)}
        )

    except:
        LOGGER_EXPORT_EXCEL.exception(f"{file_name!r}")
        return {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}

    finally:
        excel.excel_close()

    return {"OK": f"GENERATION DU FICHIER {file_name} TERMINEE AVEC SUCCES"}
