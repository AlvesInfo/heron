# pylint: disable=W0702,W1203,E1101
"""Module d'export du fichier excel pour Familles Statistiques/Axes

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
from apps.book.models.supplier_identifiers_models import StatFamillyAxes
from apps.book.excel_outputs.book_columns import columns_list_statistiques


def get_row():
    """Class qui renvoie les bonnes colonnes pour le fichier Excel"""

    yield from [
        (
            row.get("name"),
            row.get("description"),
            "X" if row.get("regex_bool") else "",
            row.get("stat_axes__invoice_column"),
            row.get("stat_axes__regex_match") or "",
            row.get("stat_axes__expected_result") or "",
            row.get("stat_axes__axe_pro__section") or "",
            row.get("stat_axes__description") or "",
            row.get("stat_axes__norme") or "",
            row.get("stat_axes__comment") or "",
            row.get("stat_axes__big_category__name") or "",
            row.get("stat_axes__sub_category__name") or "",
            row.get("stat_axes__item_weight") or "",
            row.get("stat_axes__unit_weight") or "",
            row.get("stat_axes__customs_code") or "",
        )
        for row in StatFamillyAxes.objects.all()
        .values(
            "name",
            "description",
            "regex_bool",
            "stat_axes__invoice_column",
            "stat_axes__regex_match",
            "stat_axes__expected_result",
            "stat_axes__axe_pro__section",
            "stat_axes__description",
            "stat_axes__norme",
            "stat_axes__comment",
            "stat_axes__big_category__name",
            "stat_axes__sub_category__name",
            "stat_axes__item_weight",
            "stat_axes__unit_weight",
            "stat_axes__customs_code",
        )
        .order_by("name", "stat_axes__invoice_column", "stat_axes__regex_match")
    ]


def excel_liste_statistiques(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier de liste des Familles Statistiques/Axes"""
    titre_list = file_name.split("_")
    titre = " ".join(titre_list[:-4])
    list_excel = [file_io, [titre[:30]]]
    excel = GenericExcel(list_excel)
    columns = columns_list_statistiques

    try:
        titre_page_writer(excel, 1, 0, 0, columns, titre)
        output_day_writer(excel, 1, 1, 0)
        excel.write_merge_h(1, 3, 0, 2, "Familles", columns[0].get("f_entete"))
        excel.write_merge_h(1, 3, 3, 14, "Statistiques/Axes", columns[3].get("f_entete"))
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
