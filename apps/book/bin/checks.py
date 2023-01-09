# pylint: disable=C0303,E0401,W0212
"""Module de vérifications pour l'app book

Commentaire:

created at: 2022-12-14
created by: Paulo ALVES

modified at:
modified by:
"""
from psycopg2 import sql
from django.db import connection
from apps.accountancy.models import CctSage
from apps.book.models import SupplierCct


def check_cct_identifier(cleaned_data: dict):
    """Vérification que l'identifiant saisi n'existe pas déjà dans un autre cct ou dans le même
    :param cleaned_data: les données du formulaire après validation du formulaire par django
    :return: message
    """
    before_cct_identifier = cleaned_data.get("id").cct_identifier
    before_cct_identifier = (
        before_cct_identifier[:-1] if before_cct_identifier[-1] == "|" else before_cct_identifier
    )
    before = str(before_cct_identifier).split("|")

    after_cct_identifier = cleaned_data.get("cct_identifier")
    after_cct_identifier = (
        after_cct_identifier[:-1] if after_cct_identifier[-1] == "|" else after_cct_identifier
    )

    after = str(after_cct_identifier).split("|")

    if before == after:
        message = "Vous n'avez rien modifié !"
        return False, message

    if set(before) == set(after):
        message = (
            "Vous avez ajouté un dentifiant déjà présent pour le cct : "
            f"{cleaned_data.get('id').cct_uuid_identification.cct}"
        )
        return False, message

    diff_identifier = list(set(after).difference(set(before)))

    # On vérifie si l'identifiant pour le cct existe déjà
    with connection.cursor() as cursor:
        sql_verify = sql.SQL(
            """
            select 
                    cct, cct_identifier
            from (
                select
                       third_party_num, 
                       ac.cct ,
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
                       ) as cct_identifier
                from {table_supplier} bs
                join {table_cct} ac 
                on bs.cct_uuid_identification = ac.uuid_identification 
                where third_party_num = %(third_party_num)s
            ) ident 
            where cct_identifier = ANY(%(cct_identifier)s)
            """
        ).format(
            table_supplier=sql.Identifier(SupplierCct._meta.db_table),
            table_cct=sql.Identifier(CctSage._meta.db_table),
        )
        cursor.execute(
            sql_verify,
            {
                "third_party_num": cleaned_data.get("id").third_party_num.third_party_num,
                "cct_identifier": diff_identifier,
            },
        )
        ident_list = cursor.fetchall()

        if ident_list:
            message = ""

            for cct, ident in ident_list:
                message += f"L'identifiant {ident} est déjà utilisé dans le cct {cct}   -   "

            message = message[:-7]

            return None, message

    return True, ""
