# pylint: disable=E0401,C0303
"""
FR : Module de génération identifiant des maisons pour les tiersx3 en cours d'utilisation
EN : Generation module identifying houses for tiersx3 in use

Commentaire:

created at: 2022-12-28
created by: Paulo ALVES

modified at: 2022-12-28
modified by: Paulo ALVES
"""
from psycopg2 import sql
from django.db import connection


def add_news_cct_sage():
    """Ajoute dans la table d'identification des fournisseurs book_suppliercct
    les nouveaux cct sage avec le paramétrage par défaut

    """
    with connection.cursor() as cursor:
        sql_to_create = sql.SQL(
            """
            with "suppliers" as (
                select 
                    "third_party_num"
                from (
                    select 
                        "third_party_num" 
                    from "edi_ediimport" ee 
                    union all
                    select 
                        "third_party_num"
                    from "suppliers_invoices_invoice" sii 
                ) req 
                group by "third_party_num"
            ),
            "existing" as (
                select 
                    ac."cct", 
                    ac."name", 
                    ac."short_name", 
                    ac."uuid_identification", 
                    bs."cct_uuid_identification", 
                    bs."third_party_num", 
                    bs."cct_identifier"
                from "accountancy_cctsage" ac 
                join "book_suppliercct" bs
                on ac."uuid_identification" = bs."cct_uuid_identification"
                where bs."cct_uuid_identification" is not null
            ),
            "alls" as (
                select 
                    "cct", 
                    "third_party_num", 
                    ac."uuid_identification" as "cct_uuid_identification"
                from "suppliers" ss, "accountancy_cctsage" ac
            ),
            "to_create" as (
                select 
                    now() as "created_at",
                    now() as "modified_at",
                    "cct" || '|'as "cct_identifier",
                    au."uuid_identification" as "created_by",
                    "third_party_num",
                    "cct_uuid_identification"
                    
                from "alls" aa, "auth_user" au
                where not exists (
                    select 1 
                    from "existing" ex 
                    where ex."cct" = aa."cct" 
                    and ex."third_party_num" = aa."third_party_num"
                )
                and au."username" = 'automate'
            )
            insert into "book_suppliercct"
            (
                "created_at",
                "modified_at",
                "cct_identifier",
                "created_by",
                "third_party_num",
                "cct_uuid_identification"
            )
            select 
                "created_at",
                "modified_at",
                "cct_identifier",
                "created_by",
                "third_party_num",
                "cct_uuid_identification"
            from "to_create"
            """
        )
        cursor.execute(sql_to_create)
