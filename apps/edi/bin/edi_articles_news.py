# pylint: disable=E0401,C0303
"""
FR : Module de traitement des nouveaux articles pour dans la table articles avec new_article = true
EN : New article processing module for in articles table with new_article = true

Commentaire:

created at: 2023-03-18
created by: Paulo ALVES

modified at: 2023-03-18
modified by: Paulo ALVES
"""
import os
import platform
import sys
from typing import AnyStr, Tuple

import django

BASE_DIR = r"C:\SitesWeb\heron"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")

django.setup()

from django.db import connection

SQL_FLAG_ERROR_SUB_CATEGORY = """
with "sub_cat" as (
    SELECT DISTINCT 
        "aa"."id"
    FROM "articles_article" "aa" 
    LEFT JOIN (
        SELECT 
            "uuid_big_category",
            1 as "uuid_identification"
        FROM "parameters_subcategory"
        GROUP BY "uuid_big_category"
    ) "pc"
    ON "pc"."uuid_big_category" = "aa"."uuid_big_category"
    WHERE CASE
            WHEN "aa"."uuid_big_category" = "pc"."uuid_big_category" 
                 and 
                 "aa"."uuid_sub_big_category" isnull 
            THEN true
            ELSE false
          END
)
UPDATE "articles_article" "art"
SET "error_sub_category" = CASE
                            WHEN "art"."id" in (SELECT "id" FROM "sub_cat")
                            THEN true
                            ELSE false
                          END
WHERE exists (
    SELECT 1 
    FROM "parameters_subcategory" "pp" 
    WHERE "pp"."uuid_big_category" = "art"."uuid_big_category"
)
or 
"error_sub_category" isnull
"""

SQL_FLAG_WITHOUT_AXES = """
UPDATE "articles_article" "art"
SET "new_article" = true
WHERE exists (
    select 
        1 
    from "articles_article" "aa"
    where 
        (
            "axe_bu" is null 
            or
            "axe_prj" is null
            or
            "axe_pro" is null
            or
            "axe_pys" is null
            or
            "axe_rfa" is null
            or 
            "uuid_big_category" is null
        )
        and 
        "aa"."id" = "art"."id"
)
"""

SQL_EDI_IMPORT_ARTICLES = """
update "edi_ediimport" "ee"
set "axe_bu" = "ar"."axe_bu",  
    "axe_prj" = "ar"."axe_prj",  
    "axe_pro" = "ar"."axe_pro",  
    "axe_pys" = "ar"."axe_pys",  
    "axe_rfa" = "ar"."axe_rfa",  
    "uuid_big_category" = "ar"."uuid_big_category",  
    "uuid_sub_big_category" = "ar"."uuid_sub_big_category"
from (
    select
        "reference",
        "axe_bu",
        "axe_prj",
        "axe_pro",
        "axe_pys",
        "axe_rfa",
        "uuid_big_category",
        "uuid_sub_big_category",
        "third_party_num" ,
        "new_article"
    from "articles_article" 
) "ar" 
where "ar"."reference" = "ee"."reference_article" 
and "ar"."third_party_num" = "ee"."third_party_num" 
and (
    "ar"."axe_bu" is null 
    or
    "ar"."axe_prj" is null
    or
    "ar"."axe_pro" is null
    or
    "ar"."axe_pys" is null
    or
    "ar"."axe_rfa" is null
    or 
    "ar"."uuid_big_category" is null
)
and "ar"."new_article" = false
"""


def get_famillly_edi_ediimport_new_articles(cursor: connection.cursor) -> Tuple:
    """Renvoie le nom des statitsiques à appliquer aux articles importés
    dans edi_edi_import non présents dans la table articles pour les codifier
    avec les valeurs de stats codifiées
    :param cursor: cursor de connection psycopg2 django
    :return: La liste des (tiers, nom_stat, to_regex) pour les articles dans edi_ediimport
             non présents dans la table article
    """
    sql_stats = """
    select 
        "ee"."third_party_num", 
        "bs"."stat_name"
    from "book_society" "bs"
    join "book_statfamillyaxes" "bs2"
    on "bs"."stat_name"= "bs2"."name"
    join "edi_ediimport" "ee"
    on "bs"."third_party_num"= "ee"."third_party_num"
    where not exists (
        select 
            1 
         from "articles_article" "aa"
        where "aa"."third_party_num"= "ee"."third_party_num"
          and "aa"."reference"= "ee"."reference_article"
    ) 
    group by 
        "ee"."third_party_num", 
        "bs"."stat_name", 
        "bs2"."regex_bool"
    """
    cursor.execute(sql_stats)
    return cursor.fetchall()


def set_stat_definitions(third_party_num: AnyStr, stat_name: AnyStr, cursor: connection.cursor):
    """
    Set les stats à appliquer pour les articles non présents dans la table articles
    :param third_party_num: Tiers X3
    :param stat_name: nom de la stat
    :param cursor: cursor de connection psycopg2 django
    :return:
    """
    sql_set_stat = """
    update edi_ediimport edi
    set 
        "axe_bu" = "req_stat"."axe_bu",
        "axe_prj" = "req_stat"."axe_prj",
        "axe_pro" = "req_stat"."axe_pro",
        "axe_pys" = "req_stat"."axe_pys",
        "axe_rfa" = "req_stat"."axe_rfa",
        "uuid_big_category" = "req_stat"."uuid_big_category",
        "uuid_sub_big_category" = "req_stat"."uuid_sub_big_category",
        "customs_code" = "req_stat"."customs_code",
        "item_weight" = "req_stat"."item_weight",
        "unit_weight" = "req_stat"."unit_weight"
    from (
        select distinct
            "third_party_num", 
            "reference_article", 
            (select "axe_bu" from "parameters_defaultaxearticle" "pd" limit 1) as "axe_bu",
            (select "axe_prj" from "parameters_defaultaxearticle" "pd" limit 1) as "axe_prj",
            (select "axe_pys"  from "parameters_defaultaxearticle" "pd" limit 1) as "axe_pys",
            (select "axe_rfa"  from "parameters_defaultaxearticle" "pd" limit 1) as "axe_rfa",
            "axe_pro",
            "uuid_big_category",
            "uuid_sub_big_category",
            "customs_code",
            "item_weight",
            "unit_weight",
            "bool_stat"
        from (
            select 
                "third_party_num", 
                "reference_article", 
                "famille",
                "stat"."regex_match" as "regex_match",
                "stat"."expected_result" as "expected_result",
                REGEXP_MATCHES("famille", "stat"."regex_match")::text[] as "re_match",
                (
                    REGEXP_MATCHES("famille", "stat"."regex_match")::text[] 
                    = 
                    string_to_array("stat"."expected_result", ',')
                ) as "bool_stat",
                "axe_pro",
                "stat"."uuid_big_category",
                "stat"."uuid_sub_big_category",
                "stat"."customs_code",
                "stat"."item_weight",
                "stat"."unit_weight"
            from (
                select 
                    "ee"."third_party_num", 
                    "ee"."reference_article", 
                    "ee"."famille" 
                from "edi_ediimport" "ee" 
                left join "articles_article" "aa" 
                on "ee"."reference_article" = "aa"."reference" 
                and "ee"."third_party_num" = "aa"."third_party_num"
                where "aa"."reference" is null
                and "ee"."third_party_num" = %(third_party_num)s
                group by "ee"."third_party_num" , 
                         "ee"."reference_article", 
                         "ee"."famille"
            ) "edi",
            (
                select 
                    "regex_match",
                    "expected_result",
                    "axe_pro",
                    "uuid_big_category",
                    "uuid_sub_big_category",
                    "customs_code",
                    "item_weight",
                    "unit_weight"
                from "book_supplierfamilyaxes" "bs" 
                where "stat_name" = %(stat_name)s
            ) "stat"
         ) "req_match"
         group by     
            "third_party_num", 
            "reference_article", 
            "axe_pro",
            "uuid_big_category",
            "uuid_sub_big_category",
            "customs_code",
            "item_weight",
            "unit_weight",
            "bool_stat"
         having "bool_stat" = true
    ) req_stat
    where "edi"."third_party_num" = "req_stat"."third_party_num"
      and "edi"."reference_article" = "req_stat"."reference_article"
    """
    cursor.execute(sql_set_stat, {"third_party_num": third_party_num, "stat_name": stat_name})
    print(f"fin stat_definitions : {third_party_num} - {stat_name} : {cursor.rowcount}")


def insert_new_articles(cursor: connection.cursor):
    """
    Insertion en base des nouveaux articles, flagués new articles
    :param cursor: cursor de connection psycopg2 django
    """
    sql_insert = """
    insert into "articles_article"
        (
            "created_at",
            "modified_at",
            "reference",
            "ean_code",
            "libelle",
            "item_weight",
            "customs_code",
            "catalog_price",
            "uuid_identification",
            "axe_bu",
            "axe_prj",
            "axe_pys",
            "axe_rfa",
            "axe_pro",
            "third_party_num",
            "famille",
            "uuid_big_category",
            "uuid_sub_big_category",
            "created_by",
            "packaging_qty",
            "new_article"
        )
    select 
        now() as "created_at",
        now() as "modified_at",
        "reference_article" as "reference", 
        "ee"."ean_code", 
        max("ee"."libelle") as "libelle", 
        max("ee"."item_weight") as "item_weight",
        max("ee"."customs_code") as "customs_code",
        max(coalesce("net_unit_price", 0)) as "catalog_price",
        gen_random_uuid() as "uuid_identification",
        case 
            when "ee"."axe_bu" isnull 
            then (select "axe_bu" from "parameters_defaultaxearticle" "pd" limit 1) 
            else "ee"."axe_bu"
        end as "axe_bu",
        case 
            when "ee"."axe_prj" isnull 
            then (select "axe_prj" from "parameters_defaultaxearticle" "pd" limit 1) 
            else "ee"."axe_prj"
        end as "axe_prj",
        case 
            when "ee"."axe_pys" isnull 
            then (select "axe_pys"  from "parameters_defaultaxearticle" "pd" limit 1)
            else "ee"."axe_pys"
        end as "axe_pys",
        case 
            when "ee"."axe_rfa" isnull 
            then (select "axe_rfa"  from "parameters_defaultaxearticle" "pd" limit 1)
            else "ee"."axe_rfa"
        end as "axe_rfa",
        "ee"."axe_pro",
        "ee"."third_party_num",
        "ee"."famille",
        case 
            when "ee"."uuid_big_category" isnull 
            then (select "uuid_big_category" from "parameters_defaultaxearticle" "pd" limit 1) 
            else "ee"."uuid_big_category"
        end as "uuid_big_category",
        "ee"."uuid_sub_big_category",
        (
            select 
            uuid_identification 
            from auth_user 
            where email='automate@acuitis.com' 
            limit 1
        ) as "created_by",
        1 as "packaging_qty",
        true as "new_article"
    from "edi_ediimport" "ee"
    left join "articles_article" "aa" 
    on "ee"."third_party_num" = "aa"."third_party_num"
    and "ee"."reference_article" = "aa"."reference"
    where "aa"."reference" isnull
    group by "reference_article",
            "ee"."ean_code",
            "ee"."axe_bu",
            "ee"."axe_prj",
            "ee"."axe_pys",
            "ee"."axe_rfa",
            "ee"."axe_pro",
            "ee"."third_party_num",
            "ee"."famille",
            "ee"."uuid_big_category",
            "ee"."uuid_sub_big_category"
    on conflict do nothing   
    """
    cursor.execute(sql_insert)

    nb_inserts = cursor.rowcount

    cursor.execute(SQL_FLAG_ERROR_SUB_CATEGORY)

    print(f"fin insertion des nouveaux articles : {nb_inserts}")


def set_edi_ediimport_articles(cursor: connection.cursor):
    """
    Insertion en base des nouveaux articles, flagués new articles
    :param cursor: cursor de connection psycopg2 django
    """
    sql_update = """
    update "edi_ediimport" "edi" 
    set 
        "axe_bu" = "maj"."axe_bu",
        "axe_prj" = "maj"."axe_prj",
        "axe_pro" = "maj"."axe_pro",
        "axe_pys"  = "maj"."axe_pys",
        "axe_rfa" = "maj"."axe_rfa",
        "uuid_big_category" = "maj"."uuid_big_category",
        "uuid_sub_big_category" = "maj"."uuid_sub_big_category",
        "unit_weight" = "maj"."unit_weight",
        "item_weight" = "maj"."item_weight",
        "customs_code" = "maj"."customs_code"
    from (
        select 
            "aa"."third_party_num",
            "aa"."reference" as "reference_article", 
            "aa"."axe_bu", 
            "aa"."axe_prj", 
            "aa"."axe_pro", 
            "aa"."axe_pys", 
            "aa"."axe_rfa",
            "aa"."uuid_big_category",
            "aa"."uuid_sub_big_category",
            "aa"."unit_weight",
            3 as "item_weight",
            "aa"."customs_code"
        from "edi_ediimport" "ee" 
        join "articles_article" "aa" 
        on "ee"."reference_article" = "aa"."reference" 
        and "ee"."third_party_num" = "aa"."third_party_num"
        where (
            "ee"."axe_bu" isnull
            or 
            "ee"."axe_prj" isnull
            or 
            "ee"."axe_pro" isnull
            or 
            "ee"."axe_pys" isnull
            or 
            "ee"."axe_rfa" isnull
            or 
            "ee"."uuid_big_category" isnull
        )
    ) "maj"
    where "edi"."third_party_num" = "maj"."third_party_num"
      and "edi"."reference_article" = "maj"."reference_article"
    """
    cursor.execute(sql_update)
    print(f"fin update des articles : {cursor.rowcount}")


def set_axes_with_regex() -> None:
    """
    Mise à jour des articles qui viennent d'edi_ediimport non présents dans la table article
    :return: None
    """
    with connection.cursor() as cursor:
        get_families = get_famillly_edi_ediimport_new_articles(cursor)

        for third, stat in get_families:
            set_stat_definitions(third, stat, cursor)

        insert_new_articles(cursor)
        set_edi_ediimport_articles(cursor)


if __name__ == "__main__":
    set_axes_with_regex()
