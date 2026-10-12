"""FR : Module d'update des accounts articles après création ou update.

EN : Module for updating article accounts after creation or update.

Commentaire:

created at: 2023-05-10
created by: Paulo ALVES

modified at: 2023-05-10
modified by: Paulo ALVES
"""

import uuid

from django.db import connection

from apps.core.functions import functions_setups  # noqa: F401  amorçage Django hors serveur


def delete_orphans_accounts():
    """Suppression globale des comptes dans les articles qui ne sont plus dans la table."""
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
    """Mise à jour des articles de la table edi_ediimport avec les axes de la table articles."""
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


def set_update_articles_account(article_uuid: uuid.UUID | None = None):
    """Création globale des comptes achat vente manquants pour tous les articles.

    Les comptes déjà existants ne sont jamais modifiés, seul l'écran de modification
    des articles / comptes (ArticleAccountUpdate) peut les changer.
    :param article_uuid: si c'est pour un seul article, on lui met le tiers et la référence
    :return: None.
    """
    sql_create_account = """
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
            where (
                (%(article_uuid)s is null and "aa"."new_article" = false)
                or (%(article_uuid)s is not null and "aa"."uuid_identification" = %(article_uuid)s)
            )
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
    do nothing
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_create_account, {"article_uuid": article_uuid})


def set_update_articles_confict_account():
    """Update global sans comptes achat ou vente pour tous les articles.

    :return: None.
    """
    sql_create_account = """
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
            where
            ( "ae"."article"::varchar
                ||
                  "ae"."vat"::varchar
                  ||
                  "ae"."child_center"::varchar
            )::varchar
            =
            (
                "aa"."uuid_identification"::varchar
                ||
                "cpa"."vat"::varchar
                ||
                "cpa"."child_center"::varchar
            )::varchar
        )
    )
    on conflict do nothing
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_create_account)


if __name__ == "__main__":
    delete_orphans_accounts()
    set_update_articles_account()
