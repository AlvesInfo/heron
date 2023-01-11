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


def add_news_cct_sage(third_party_num: str = None, force_add=False):
    """Ajoute dans la table d'identification des fournisseurs book_suppliercct
    les nouveaux cct sage avec le paramétrage par défaut
    :param third_party_num: N° de tiers X3
    :param force_add: Ajout forcé du tiers même si il ne fait pas partie des fournisseurs courants
    :return: None
    """
    with connection.cursor() as cursor:
        condition = (
            'and "third_party_num" = %(third_party_num)s'
            if third_party_num
            else 'and "third_party_num" is not null'
        )
        force_select = (
            f"""
            union all
            select '{third_party_num}'
            """
            if third_party_num and force_add
            else ""
        )
        sql_to_create = sql.SQL(
            f"""
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
                    {force_select}
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
                    "cct_uuid_identification",
                    "cct"
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
            from "to_create" tc
            where exists (
                    select 1 
                    from "centers_clients_maison" cc 
                    where cc."cct" = tc."cct"
                    and closing_date isnull
                )
              and not exists (
                    select 1 
                    from (
                        select 
                            "third_party_num", 
                            unnest(string_to_array("cct_identifier", '|')) as "cct" 
                        from "book_suppliercct"
                    ) bs where bs."cct" = tc."cct" 
                    and bs."third_party_num" = tc."third_party_num"
                )
            {condition}
            """
        )
        if condition:
            cursor.execute(sql_to_create, {"third_party_num": third_party_num})
        else:
            cursor.execute(sql_to_create)


def update_edi_import_cct_uui_identifiaction(
    force_update: bool = False, third_party_num: str = None
):
    """Mise à jour du champ cct_uui_identifiaction de la table edi_import,
    après mise à jour des suppliers_cct. Ou par appel de la fonction.
    force_update = False, on fait la mise à jour des lignes ou le cct_uuid_identification est null.
    force_update = True, on fait la mise à jour de toutes lignes.
    :param force_update: Booléen True ou False
    :param third_party_num: third_party_num qui change ce cct
    :return: None
    """
    with connection.cursor() as cursor:
        alls = ' and edi."cct_uuid_identification" isnull ' if force_update else ""
        third_party_num_filter = (
            'and ei."third_party_num" = %(third_party_num)s' if third_party_num else ""
        )
        sql_update = sql.SQL(
            f"""
             update "edi_ediimport" edi
             set "cct_uuid_identification" = cc."cct_uuid_identification"
             from (
               select
                     ei."id", re."cct_uuid_identification"
               from "edi_ediimport" ei
               left join (
                     select
                            ee."id", 
                            ee."third_party_num", 
                            ee."supplier", 
                            ee."code_fournisseur", 
                            ee."maison", 
                            ee."code_maison", 
                            bs."cct_identifier", 
                            bs."cct_uuid_identification"
                 from "edi_ediimport" ee
                 left join (
                        select
                           bsp."third_party_num", 
                           ccm."uuid_identification" as "cct_uuid_identification", 
                           unnest(
                                string_to_array(
                                    case 
                                        when right("cct_identifier", 1) = '|' 
                                        then left("cct_identifier", length("cct_identifier")-1) 
                                        else "cct_identifier"
                                    end
                                    , 
                                    '|'
                                )
                           ) as "cct_identifier"
                        from "book_suppliercct" bsp
                        join "accountancy_cctsage" ac 
                        on bsp."cct_uuid_identification" = ac."uuid_identification" 
                        join "centers_clients_maison" ccm
                        on ac."cct" = ccm."cct"
                     ) bs
                     on ee."third_party_num" = bs."third_party_num"
                     where ee."third_party_num" = bs."third_party_num"
                     and ee."code_maison" = bs."cct_identifier"
               ) re
               on ei."id" = re."id"
               where "cct_identifier" is not null
               {third_party_num_filter}
            ) cc
            where edi."id" = cc."id"
            and "valid" = true
            {alls}
            """
        )

        if third_party_num:
            cursor.execute(sql_update, {"third_party_num": third_party_num})
        else:
            cursor.execute(sql_update)
