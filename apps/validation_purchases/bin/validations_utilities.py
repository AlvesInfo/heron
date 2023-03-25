# pylint: disable=E0401
"""
FR : Module des utilitaires pour la validation
EN : Utilities Modul for validation

Commentaire:

created at: 2023-25-25
created by: Paulo ALVES

modified at: 2023-25-25
modified by: Paulo ALVES
"""
from typing import AnyStr

from django.db import connection


def set_is_multi_store(third_party_num: AnyStr, invoice_number: AnyStr, invoice_year: int):
    """
    Update des lignes de factures edi_ediimport, sur le champ multistore
    :param third_party_num: Tiers X3
    :param invoice_number: N° de Facture
    :param invoice_year: Année de facture
    :return:
    """
    with connection.cursor() as cursor:
        sql_update = """
        update "edi_ediimport" "edi"
        set "is_multi_store"= case 
                                when "req"."nbre" = 1 
                                then false
                                else true
                              end
        from (
            select 
                sum("nbre") as "nbre",
                "third_party_num",
                "invoice_number",
                "invoice_year"
            from (
                select 
                    1 as nbre, 
                    "third_party_num",
                    "invoice_number",
                    "invoice_year"
                from "edi_ediimport" 
                where"third_party_num" = %(third_party_num)s
                  and "invoice_number" = %(invoice_number)s
                  and "invoice_year" = %(invoice_year)s
                group by "cct_uuid_identification",
                         "third_party_num",
                         "invoice_number",
                         "invoice_year"
            ) "regroup"
            group by "third_party_num",
                     "invoice_number",
                     "invoice_year"
        ) "req"
        where "edi"."third_party_num" = "req"."third_party_num"
          and "edi"."invoice_number" = "req"."invoice_number"
          and "edi"."invoice_year" = "req"."invoice_year"
        """
        cursor.execute(
            sql_update,
            {
                "third_party_num": third_party_num,
                "invoice_number": invoice_number,
                "invoice_year": invoice_year,
            },
        )
