# pylint: disable=E0401,C0413,R0914
"""
FR : Module de post traitement après import data
EN : Post-processing module after data import

Commentaire:

created at: 2023-07-02
created by: Paulo ALVES

modified at: 2023-07-02
modified by: Paulo ALVES
"""
from psycopg2 import sql
from django.db import connection


def duplicates_delete_accounts():
    """Supprime les doublons de la table AccountsAxeProCategory, car dans les clefs,
    il y a le champ, subcategory qui peut être null
    """
    with connection.cursor() as cursor:
        sql_duplicates_delete = sql.SQL(
            """
            delete from "centers_purchasing_accountsaxeprocategory" "cpa"
            where "cpa"."id" in (
                select 
                    "ca"."id"
                from "centers_purchasing_accountsaxeprocategory" "ca"
                join ( 
                    select 
                        min("id") as "pk",
                        "child_center",
                        "uuid_big_category",
                        coalesce("uuid_sub_category"::varchar, '') as "uuid_sub_category",
                        "axe_pro",
                        "vat"
                    from "centers_purchasing_accountsaxeprocategory"  
                    group by "child_center",
                             "uuid_big_category",
                             coalesce("uuid_sub_category"::varchar, ''),
                             "axe_pro",
                             "vat"
                    having count(*) > 1
                ) "cp"
               on "ca"."child_center" = "cp"."child_center" 
               and "ca"."uuid_big_category" = "cp"."uuid_big_category" 
               and (
                        coalesce("ca"."uuid_sub_category"::varchar, '') 
                        = 
                        coalesce("cp"."uuid_sub_category"::varchar, '')
                ) 
               and "ca"."axe_pro" = "cp"."axe_pro" 
               and "ca"."vat" = "cp"."vat" 
               where "ca"."id" != "cp"."pk"
            )
            """
        )
        cursor.execute(sql_duplicates_delete)
