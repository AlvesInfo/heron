# pylint: disable=W0702,W1203,E0401,E1101
"""Module d'export de la liste des articles excel

Commentaire:

created at: 2022-05-12
created by: Paulo ALVES

modified at: 2022-05-12
modified by: Paulo ALVES
"""
import io

from django.db.models import Q

from heron.loggers import LOGGER_EXPORT_EXCEL
from apps.core.functions.functions_excel import GenericExcel
from apps.core.excel_outputs.excel_writer import (
    titre_page_writer,
    output_day_writer,
    columns_headers_writer,
    sheet_formatting,
    rows_writer,
)
from apps.articles.excel_outputs.output_excel_articles_columns import columns_list_articles_news
from apps.articles.models import Article


def get_clean_rows() -> iter:
    """Retourne les lignes à écrire"""

    return [
        (
            f"{row.get('third_party_num', '')} - {row.get('third_party_num', '')}",
            row.get("reference", ""),
            row.get("libelle", ""),
            row.get("axe_bu__section", ""),
            row.get("axe_prj__section", ""),
            row.get("axe_pro__section", ""),
            row.get("axe_pys__section", ""),
            row.get("axe_rfa__section", ""),
            row.get("big_category__name", ""),
            row.get("sub_category__name", ""),
            row.get("item_weight", ""),
            row.get("unit_weight__unity", ""),
            row.get("customs_code", ""),
        )
        for row in Article.objects.filter(
            Q(axe_bu__isnull=True)
            | Q(axe_prj__isnull=True)
            | Q(axe_pro__isnull=True)
            | Q(axe_pys__isnull=True)
            | Q(axe_rfa__isnull=True)
            | Q(big_category__isnull=True)
            | Q(new_article=True)
        ).values(
            "third_party_num",
            "third_party_num__short_name",
            "reference",
            "libelle",
            "axe_bu__section",
            "axe_prj__section",
            "axe_pro__section",
            "axe_pys__section",
            "axe_rfa__section",
            "big_category__name",
            "sub_category__name",
            "item_weight",
            "unit_weight__unity",
            "customs_code",
        )
    ]


def excel_liste_articles_news(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier de la liste des nouveaux articles excel"""
    titre = "LISTE DE NOUVEAUX ARTICLES"
    list_excel = [file_io, [titre[:30]]]
    excel = GenericExcel(list_excel)
    columns = columns_list_articles_news

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
