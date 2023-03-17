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


@transaction.atomic
def update_supplier_cct_reference_coisium():
    """Fonction d'update des cct depuis book_supplier_cct,
    au changement de reference Cosium dans les clients Maisons
    """
    sql_reference_cosium = """
    update "book_suppliercct" "bs"
    set "cct_identifier" = case 
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
        cursor.execute(sql_reference_cosium)
