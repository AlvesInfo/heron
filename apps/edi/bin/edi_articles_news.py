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

from apps.parameters.models import DefaultAxeArticle


def get_famillly_edi_ediimport_new_articles(cursor: connection.cursor) -> Tuple:
    """Renvoie le nom des statitsiques à appliquer aux artciles importés
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


def get_axes_default():
    """
    Retourne les axes et la grande catégorie par défaut
    :return: ("axe_bu", "axe_prj", "axe_pys", "axe_rfa", "big_category")
    """
    axes_default = (
        DefaultAxeArticle.objects.all()
        .values("axe_bu", "axe_prj", "axe_pys", "axe_rfa", "big_category")
        .first()
    )
    if axes_default:
        return axes_default

    return {"axe_bu": None, "axe_prj": None, "axe_pys": None, "axe_rfa": None, "big_category": None}


def set_stat_definitions(third_party_num: AnyStr, stat_name: AnyStr):
    """
    Set les stats à appliquer pour les articles non présents dans la table articles
    :param third_party_num: Tiers X3
    :param stat_name: nom de la stat
    :return:
    """
    sql_get_stat = """
    select 
        third_party_num, 
        reference_article, 
        axe_pro,
        uuid_big_category,
        uuid_sub_big_category,
        customs_code,
        item_weight,
        unit_weight
    from (
        select 
            third_party_num , 
            reference_article, 
            famille,
            stat.regex_match as regex_match,
            stat.expected_result as expected_result,
            REGEXP_MATCHES(famille, stat.regex_match)::text[] as re_match,
            REGEXP_MATCHES(famille, stat.regex_match)::text[] = string_to_array(stat.expected_result, ',') as test_stat,
            axe_pro,
            stat.uuid_big_category,
            stat.uuid_sub_big_category,
            stat.customs_code,
            stat.item_weight,
            stat.unit_weight
        from (
           select 
            ee.third_party_num, 
            ee.reference_article, 
            ee.famille 
           from edi_ediimport ee 
           left join articles_article aa 
           on ee.reference_article = aa.reference 
           where aa.reference is null
           and ee.third_party_num = 'ALCO001'
           group by ee.third_party_num , ee.reference_article, famille
        ) edi,
        (
            select 
                regex_match,
                expected_result,
                axe_pro,
                uuid_big_category,
                uuid_sub_big_category,
                customs_code,
                item_weight,
                unit_weight
            from book_supplierfamilyaxes bs 
            where stat_name = 'ALCO001'
        ) stat
     ) req_match
     where test_stat
     group by     
        third_party_num, 
        reference_article, 
        axe_pro,
        uuid_big_category,
        uuid_sub_big_category,
        customs_code,
        item_weight,
        unit_weight
    having count(reference_article) = 1
    """


def set_axes_with_regex() -> None:
    """
    Mise à jour des articles qui viennent d'edi_ediimport non présents dans la table article
    :return: None
    """
    with connection.cursor() as cursor:
        get_families = get_famillly_edi_ediimport_new_articles(cursor)

        for row in get_families:
            third, stat = row
            print(third, stat)


if __name__ == "__main__":
    set_axes_with_regex()
