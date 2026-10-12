"""Module d'export de la liste des articles excel.

Commentaire:

created at: 2022-05-12
created by: Paulo ALVES

modified at: 2022-05-12
modified by: Paulo ALVES
"""

import io
from collections.abc import Iterator

from django.db import connection
from psycopg2 import sql

from apps.articles.excel_outputs.output_excel_articles_columns import columns_list_articles
from apps.book.models import Society
from apps.core.excel_outputs.generic_list_export import excel_list_export
from apps.parameters.models import Category


def get_clean_rows(third_party_num: str, category: str) -> Iterator:
    """Retourne les lignes à écrire."""
    sql_query = sql.SQL(
        """
        select
            "aa"."reference",
            "aa"."libelle",
            "aa"."libelle_heron",
            "aa"."brand",
            "aa"."manufacturer",
            "pc"."ranking" || ' - ' || "pc"."name" as "big_category",
            "ps"."name" as "sub_familly",
            "aa"."budget_code",
            "aa"."famille_supplier",
            "as2"."section" as "axe_bu",
            "as3"."section" as "axe_prj",
            "as4"."section" as "axe_pro",
            "as5"."section" as "axe_pys",
            "as6"."section" as "axe_rfa",
            "aa"."made_in",
            "aa"."customs_code",
            case when "aa"."new_article" = true then 'X' else '' end as "new_article",
            "aa"."comment"
        from "articles_article" "aa"
        join "book_society" "bs"
        on "aa"."third_party_num" = "bs"."third_party_num"
        join "parameters_category" "pp"
        on "aa"."uuid_big_category" = "pp"."uuid_identification"
        left join "accountancy_sectionsage" "as2"
        on "aa"."axe_bu" = "as2"."uuid_identification"
        left join "accountancy_sectionsage" "as3"
        on "aa"."axe_prj"  = "as3"."uuid_identification"
        left join "accountancy_sectionsage" "as4"
        on "aa"."axe_pro"  = "as4"."uuid_identification"
        left join "accountancy_sectionsage" "as5"
        on "aa"."axe_pys" = "as5"."uuid_identification"
        left join "accountancy_sectionsage" "as6"
        on "aa"."axe_rfa" = "as6"."uuid_identification"
        left join "parameters_category" "pc"
        ON "aa"."uuid_big_category" = "pc"."uuid_identification"
        left join "parameters_subfamilly" "ps"
        on "aa"."uuid_sub_familly" = "ps"."uuid_identification"
        where "aa"."third_party_num" = %(third_party_num)s
        and "pp"."slug_name"= %(category)s
        """
    )

    with connection.cursor() as cursor:
        cursor.execute(
            sql_query,
            {
                "third_party_num": third_party_num,
                "category": category,
            },
        )
        return cursor.fetchall()


def excel_liste_articles(
    file_io: io.BytesIO, file_name: str, third_party_num: str, category: str
) -> dict:
    """Fonction de génération du fichier de la liste des articles excel."""
    categorie_name = Category.objects.get(slug_name=category)
    titre_list = file_name.split("_")
    titre = (
        " ".join(titre_list[:-4])
        + f" DU FOURNISSEUR : {Society.objects.get(third_party_num=third_party_num)!s}"
        f" - Catégorie : {categorie_name.name}"
    )
    columns = columns_list_articles

    return excel_list_export(
        file_io,
        file_name,
        sheet_name=titre[:30],
        title=titre,
        columns=columns,
        rows=get_clean_rows(third_party_num, category),
        orientation="landscape",
    )
