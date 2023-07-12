# pylint: disable=W0702,W1203,E0401,E1101
"""Module d'export de la liste des articles sans comptes comptablesexcel

Commentaire:

created at: 2022-05-29
created by: Paulo ALVES

modified at: 2022-05-29
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
from apps.articles.excel_outputs.output_excel_articles_columns import (
    columns_list_articles_without_account,
)
from apps.articles.parameters.querysets import articles_without_account_queryset


def get_clean_rows() -> iter:
    """Retourne les lignes à écrire"""

    query_columns = {
        "code_center",
        "third_party_num",
        "tiers",
        "reference",
        "libelle",
        "pro",
        "category",
        "rubrique",
        "article",
        "vat_vat",
        "vat_reg"
    }
    rows = [
        {key: value for key, value in row.__dict__.items() if key in query_columns}
        for row in articles_without_account_queryset
    ]

    return [
        (
            str(row.get("article", "")),
            row.get("code_center", ""),
            row.get('third_party_num', ''),
            row.get('tiers', ''),
            row.get('reference', ''),
            row.get('libelle', ''),
            row.get("pro", ""),
            row.get("category", ""),
            row.get("rubrique", ""),
            row.get("vat_vat", ""),
            row.get("vat_reg", ""),
            "",
            "",
        )
        for row in rows
    ]


def excel_liste_articles_without_account(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier de la liste des articles sans copte comptable excel"""
    titre = "LISTE DE ARTICLES SANS COMPTES"
    list_excel = [file_io, [titre[:30]]]
    excel = GenericExcel(list_excel)
    columns = columns_list_articles_without_account

    try:
        titre_page_writer(excel, 1, 0, 0, columns, titre)
        output_day_writer(excel, 1, 1, 0)
        columns_headers_writer(excel, 1, 3, 0, columns)
        f_lignes = [dict_row.get("f_ligne") for dict_row in columns]
        f_lignes_odd = [
            {**dict_row.get("f_ligne"), **{"bg_color": "#D9D9D9"}} for dict_row in columns
        ]
        rows_writer(excel, 1, 4, 0, get_clean_rows(), f_lignes, f_lignes_odd)
        sheet_formatting(
            excel, 1, columns, {"sens": "landscape", "repeat_row": (0, 5), "fit_page": (1, 0)}
        )

    except:
        LOGGER_EXPORT_EXCEL.exception(f"{file_name!r}")
        return {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}

    finally:
        excel.excel_close()

    return {"OK": f"GENERATION DU FICHIER {file_name} TERMINEE AVEC SUCCES"}
