# pylint: disable=E0401,C0303
"""
FR : Module de gestion des Maisons
EN : Operation Module for Maisons

Commentaire:

created at: 2023-03-17
created by: Paulo ALVES

modified at: 2023-03-17
modified by: Paulo ALVES
"""
from django.db import connection, transaction
from apps.book.models import SupplierCct


@transaction.atomic
def update_supplier_cct_reference_cosium(reference_cosium):
    """Fonction d'update des cct depuis book_supplier_cct,
    au changement de reference Cosium dans les clients Maisons
    :param reference_cosium: reference Cosium
    :return: view
    """
    sql_delete_reference_cosium = """
    update "book_suppliercct" "bs"
    set "cct_identifier" = case 
                                when "bs"."cct_identifier" ilike %(reference_cosium_ilike_pipe)s
                                then REPLACE("bs"."cct_identifier", %(reference_cosium_pipe)s, '')
                                when "bs"."cct_identifier" ilike %(reference_cosium_ilike)s
                                then REPLACE("bs"."cct_identifier", %(reference_cosium)s, '')
                                else "bs"."cct_identifier"
                           end
    where "bs"."third_party_num" = 'COSI001'
    """
    sql_reference_cosium = """
    update "book_suppliercct" "bs"
    set "cct_identifier" = case
                            when "bs"."cct_identifier" isnull
                            then "cosi"."reference_cosium" || '|'
                            when right("bs"."cct_identifier", 1) = '|'
                            then "bs"."cct_identifier" || "cosi"."reference_cosium" || '|'
                            else "bs"."cct_identifier" || '|' || "cosi"."reference_cosium" || '|'
                         end

    from (
        select
           "bsp"."third_party_num",
           "ac"."uuid_identification" as "cct_uuid_identification",
           "ccm"."reference_cosium"
        from "book_suppliercct" "bsp"
        join "accountancy_cctsage" "ac"
        on "bsp"."cct_uuid_identification" = "ac"."uuid_identification"
        join "centers_clients_maison" "ccm"
        on "ac"."cct" = "ccm"."cct"
        where "bsp"."third_party_num" = 'COSI001'
        and "ccm"."reference_cosium" not in (select unnest(
                string_to_array(
                    case
                        when right("cct_identifier", 1) = '|'
                        then left("cct_identifier", length("cct_identifier")-1)
                        else "cct_identifier"
                    end
                    ,
                    '|'
                )
           ))
        and "ccm"."reference_cosium" is not null
        and  "ccm"."reference_cosium" != ''
    ) "cosi"
    where "cosi"."third_party_num" = "bs"."third_party_num"
    and "cosi"."cct_uuid_identification" = "bs"."cct_uuid_identification"
    """
    with connection.cursor() as cursor:
        # print(
        #     cursor.mogrify(
        #         sql_delete_reference_cosium,
        #         {
        #             "reference_cosium_ilike_pipe": f"%{reference_cosium}|%",
        #             "reference_cosium_pipe": f"{reference_cosium}|",
        #             "reference_cosium_ilike": f"%{reference_cosium}%",
        #             "reference_cosium": reference_cosium,
        #             "cct": cct.uuid_identification,
        #         },
        #     ).decode()
        # )
        # print(cursor.mogrify(sql_reference_cosium).decode())
        cursor.execute(
            sql_delete_reference_cosium,
            {
                "reference_cosium_ilike_pipe": f"%{reference_cosium}|%",
                "reference_cosium_pipe": f"{reference_cosium}|",
                "reference_cosium_ilike": f"%{reference_cosium}%",
                "reference_cosium": reference_cosium,
            },
        )
        cursor.execute(sql_reference_cosium)
