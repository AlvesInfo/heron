"""Module d'export de la liste des articles excel.

Commentaire:

created at: 2022-05-12
created by: Paulo ALVES

modified at: 2022-05-12
modified by: Paulo ALVES
"""

import io

from django.db.models import Q

from apps.articles.excel_outputs.output_excel_articles_columns import columns_list_articles_news
from apps.articles.models import Article
from apps.core.excel_outputs.generic_list_export import excel_list_export


def get_clean_rows() -> list:
    """Retourne les lignes à écrire."""
    return [
        (
            f"{row.get('third_party_num', '')} - {row.get('third_party_num__short_name') or ''}",
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
            "X" if row.get("error_sub_category", "") else "",
        )
        for row in Article.objects.filter(Q(new_article=True) | Q(error_sub_category=True))
        .values(
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
            "error_sub_category",
        )
        .values(
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
            "error_sub_category",
        )
    ]


def excel_liste_articles_news(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier de la liste des nouveaux articles excel."""
    titre = "LISTE DE NOUVEAUX ARTICLES"
    columns = columns_list_articles_news

    return excel_list_export(
        file_io,
        file_name,
        sheet_name=titre[:30],
        title=titre,
        columns=columns,
        rows=get_clean_rows(),
        orientation="landscape",
    )
