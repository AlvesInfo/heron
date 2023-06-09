# pylint: disable=E0401,C0413
"""
FR : Module d'update des accounts articles après création ou update
EN : Module for updating article accounts after creation or update

Commentaire:

created at: 2023-05-10
created by: Paulo ALVES

modified at: 2023-05-10
modified by: Paulo ALVES
"""
import os
import platform
import sys
import uuid

import django

BASE_DIR = r"C:\SitesWeb\heron"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")

django.setup()

from django.db import connection


def delete_orphans_accounts():
    """Suppression globale des comptes dans les articles qui ne sont plus dans la table"""
    sql_delete_not_exists_account = """
    delete from "articles_articleaccount" "arta"
    where "arta"."id" in (
        select 
            "article"
        from (
            select 
                "aa2"."id" as "article",
                "aa"."axe_pro", 
                "aa"."uuid_big_category", 
                coalesce("aa"."uuid_sub_big_category"::varchar, '') as "uuid_sub_category", 
                "aa2"."vat", 
                "aa2"."child_center" 
            from "articles_article" "aa" 
            join "articles_articleaccount" "aa2" 
            on "aa2"."article" = "aa"."uuid_identification" 
        ) "req"
        where not exists (
            select 1 
            from "centers_purchasing_accountsaxeprocategory" "cpa"
            where "cpa"."axe_pro" = "req"."axe_pro"
            and "cpa"."uuid_big_category" = "req"."uuid_big_category"
            and coalesce("cpa"."uuid_sub_category"::varchar, '') = "req"."uuid_sub_category"
            and "cpa"."vat" = "req"."vat"
            and "cpa"."child_center" = "req"."child_center"
        )
    )
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_delete_not_exists_account)


def update_axes_edi():
    """Mise à jour des articles de la table edi_ediimport avec les axes de la table articles"""
    sql_update_edi_articles = """
    update "edi_ediimport" "edi"
    set "axe_bu" = "req"."axe_bu",
        "axe_prj" = "req"."axe_prj",
        "axe_pro" = "req"."axe_pro",
        "axe_pys" = "req"."axe_pys",
        "axe_rfa" = "req"."axe_rfa",
        "uuid_big_category" = "req"."uuid_big_category",
        "uuid_sub_big_category" = "req"."uuid_sub_big_category"
    from (
        select 
            "ee"."id",
            "aa"."axe_bu",
            "aa"."axe_prj",
            "aa"."axe_pro",
            "aa"."axe_pys",
            "aa"."axe_rfa",
            "aa"."uuid_big_category",
            "aa"."uuid_sub_big_category"
        from "edi_ediimport" "ee" 
        left join "articles_article" "aa" 
        on "ee"."third_party_num" = "aa"."third_party_num" 
        and "ee"."reference_article" = "aa"."reference" 
        where "ee"."axe_bu" != "aa"."axe_bu"
        or "ee"."axe_prj" != "aa"."axe_prj"
        or "ee"."axe_pro" != "aa"."axe_pro"
        or "ee"."axe_pys" != "aa"."axe_pys"
        or "ee"."axe_rfa" != "aa"."axe_rfa"
        or "ee"."uuid_big_category" != "aa"."uuid_big_category"
        or (
            coalesce("ee"."uuid_sub_big_category"::varchar, '') 
            != 
            coalesce("aa"."uuid_sub_big_category"::varchar, '')
        )
    ) "req" 
    where "edi"."id" = "req"."id"
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_update_edi_articles)


def set_update_articles_account(article_uuid: uuid.UUID = None):
    """
    Update global des comptes achat vente pour tous les articles
    :param article_uuid: si c'est pour un seul article, on lui met le tiers et la référence
    :return: None
    """
    if article_uuid is None:
        clause_where = 'where "aa"."new_article" = false'
    else:
        clause_where = f"""where "aa"."uuid_identification" = '{article_uuid}'::uuid """

    sql_create_account = f"""
    insert into "articles_articleaccount" 
    (
        "created_at",
        "modified_at",
        "purchase_account",
        "sale_account",
        "article",
        "vat",
        "child_center"
    )
    (
        select
            now() as "created_at",	
            now() as "modified_at",
            "purchase_account", 
            "sale_account", 
            "article", 
            "vat",
            "child_center"
        from (
            select
                "aa2"."account" as "purchase_account", 
                "aa3"."account" as "sale_account", 
                "aa"."uuid_identification" as "article", 
                "cpa"."vat",
                "cpa"."child_center"
            from "articles_article" "aa" 
            join "centers_purchasing_accountsaxeprocategory" "cpa" 
            on "cpa"."axe_pro" = "aa"."axe_pro" 
            and "aa"."uuid_big_category" = "cpa"."uuid_big_category" 
            and (
                coalesce("aa"."uuid_sub_big_category"::varchar, '')
                =
                coalesce("cpa"."uuid_sub_category"::varchar, '')
            )
            left join "accountancy_accountsage" "aa2" 
            on "aa2"."uuid_identification" = "cpa"."purchase_account_uuid" 
            left join "accountancy_accountsage" "aa3" 
            on "aa3"."uuid_identification" = "cpa"."sale_account_uuid" 
            {clause_where}
            group by "aa2"."account" , 
                "aa3"."account", 
                "aa"."uuid_identification", 
                "cpa"."vat",
                "cpa"."child_center"
        ) gr
    )
    on conflict ( 
        "article", 
        "vat", 
        "child_center"
    ) 
    do update set "modified_at" = EXCLUDED."modified_at",
    "purchase_account" = EXCLUDED."purchase_account",
    "sale_account" = EXCLUDED."sale_account"
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_create_account)


def set_update_articles_confict_account():
    """
    Update global sans comptes achat vente pour tous les articles
    :return: None
    """

    sql_create_account = f"""
    insert into "articles_articleaccount" 
    (
        "created_at",
        "modified_at",
        "purchase_account",
        "sale_account",
        "article",
        "vat",
        "child_center"
    )
    (
        select
            now() as "created_at",	
            now() as "modified_at",
            "purchase_account", 
            "sale_account", 
            "article", 
            "vat",
            "child_center"
        from (
            select
                "aa2"."account" as "purchase_account", 
                "aa3"."account" as "sale_account", 
                "aa"."uuid_identification" as "article", 
                "cpa"."vat",
                "cpa"."child_center"
            from "articles_article" "aa" 
            join "centers_purchasing_accountsaxeprocategory" "cpa" 
            on "cpa"."axe_pro" = "aa"."axe_pro" 
            and "aa"."uuid_big_category" = "cpa"."uuid_big_category" 
            and (
                coalesce("aa"."uuid_sub_big_category"::varchar, '')
                =
                coalesce("cpa"."uuid_sub_category"::varchar, '')
            )
            left join "accountancy_accountsage" "aa2" 
            on "aa2"."uuid_identification" = "cpa"."purchase_account_uuid" 
            left join "accountancy_accountsage" "aa3" 
            on "aa3"."uuid_identification" = "cpa"."sale_account_uuid" 
            where not exists (
                select 1
                from "articles_articleaccount" "ae"
                where "ae"."article" = "aa"."uuid_identification"
                  and "ae"."vat" = "cpa"."vat"
                  and "ae"."child_center" = "cpa"."child_center"
            )
        ) gr
    )
    on conflict do nothing
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_create_account)


if __name__ == "__main__":
    delete_orphans_accounts()
    set_update_articles_account()
