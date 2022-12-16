# pylint: disable=C0303,E0401
"""
FR : Module des strings sql pour les validations
EN : Sql strings module for validations

Commentaire:

created at: 2022-12-16
created by: Paulo ALVES

modified at: 2022-12-16
modified by: Paulo ALVES
"""
from psycopg2 import sql

sql_edi_import_duplicates = sql.SQL(
    """
    with alls as (
        select 
            max("created_at") as "created_at", 
            "uuid_identification", 
            "third_party_num", 
            "invoice_number", 
            "invoice_year" 
          from "edi_ediimport" ee 
          where "delete" = false
         group by "uuid_identification", 
            "third_party_num", 
            "invoice_number", 
            "invoice_year"
    ),
    doublons as (
        select 
            "third_party_num", 
            "invoice_number", 
            "invoice_year"
          from "alls" aa
         group by "third_party_num", 
            "invoice_number" , 
            "invoice_year"
        having count(*) > 1
    ),
    max_alls as (
        select 
            max("created_at") as "created_at", 
            "third_party_num", 
            "invoice_number", 
            "invoice_year"
          from "alls"
         group by "third_party_num", 
            "invoice_number", 
            "invoice_year" 
    )
    select 
        al."uuid_identification",
        dd."third_party_num",
        dd."invoice_number",
        dd."invoice_year"
     from "doublons" dd 
     join "alls" al
       on dd."third_party_num" = al."third_party_num"
      and dd."invoice_number" = al."invoice_number"
      and dd."invoice_year" = al."invoice_year"
    where exists (
        select 1 
         from "max_alls" ma 
        where ma."third_party_num" = al."third_party_num"
          and ma."invoice_number" = al."invoice_number"
          and ma."invoice_year" = al."invoice_year"
          and ma."created_at" = al."created_at"
    )
"""
)

sql_invoices_duplicates = sql.SQL(
    """
    select 
        ee."uuid_identification", 
        sii."third_party_num", 
        sii."invoice_number", 
        sii."invoice_year" 
      from (
        select 
            "uuid_identification",
            "third_party_num",
            "invoice_number",
            "invoice_year"
          from "edi_ediimport" 
         where "delete" = false
         group by "uuid_identification", 
            "third_party_num", 
            "invoice_number", 
            "invoice_year"
      ) ee 
      join "suppliers_invoices_invoice" sii
        on ee."third_party_num" = sii."third_party_num"
       and ee."invoice_number" = sii."invoice_number"
       and ee."invoice_year" = sii."invoice_year"
"""
)
