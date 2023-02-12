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
    ),
    results as (
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
   )
   select 
        "uuid_identification", 
        array_agg(
            (
                '(Tiers : '||"third_party_num"||
                ' - Fac. N° : '||"invoice_number"||
                ' - Année : '|| "invoice_year"||')'
            )
        ) as commentaire,
        array_agg(("third_party_num"||'||'||"invoice_number"||'||'|| "invoice_year")) as couples
   from results
   group by "uuid_identification"
"""
)
sql_edi_import_duplicates_delete = sql.SQL(
    """
with alls as (
    select 
        max("created_at") as "created_at", 
        "uuid_identification",
        "third_party_num", 
        "invoice_number", 
        "invoice_year" 
      from "edi_ediimport" ee 
     group by
         "uuid_identification",
        "third_party_num", 
        "invoice_number", 
        "invoice_year"
),
max_keep as (
    select 
        max("created_at") as "created_at",
        "third_party_num",
        "invoice_number",
        "invoice_year"
    from alls
    group by 
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
results as (
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
    where not exists (
        select 1 
         from "max_keep" ma 
        where ma."third_party_num" = al."third_party_num"
          and ma."invoice_number" = al."invoice_number"
          and ma."invoice_year" = al."invoice_year"
          and ma."created_at" = al."created_at"
        )
   )
    delete from "edi_ediimport" ei 
    where exists (
        select 1 from "results" re 
        where ei."uuid_identification" = re."uuid_identification"
        and ei."third_party_num" = re."third_party_num"
        and ei."invoice_number" = re."invoice_number"
        and ei."invoice_year" = re."invoice_year"
    )
    """
)

sql_invoices_duplicates = sql.SQL(
    """
    with results as (
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
          join "invoices_invoice" sii
            on ee."third_party_num" = sii."third_party_num"
           and ee."invoice_number" = sii."invoice_number"
           and ee."invoice_year" = sii."invoice_year"
    )
    select 
        "uuid_identification", 
        array_agg(
            (
                '(Tiers : '||"third_party_num"||
                ' - Fac. N° : '||"invoice_number"||
                ' - Année : '|| "invoice_year"||')'
            )
        ) as commentaire,
        array_agg(("third_party_num"||'||'||"invoice_number"||'||'|| "invoice_year")) as couples
   from results
   group by "uuid_identification"
"""
)

sql_invoices_duplicates_delete = sql.SQL(
    """
    with results as (
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
          join "invoices_invoice" sii
            on ee."third_party_num" = sii."third_party_num"
           and ee."invoice_number" = sii."invoice_number"
           and ee."invoice_year" = sii."invoice_year"
    )
    delete from "edi_ediimport" ei 
    where exists (
        select 1 from "results" re 
        where ei."uuid_identification" = re."uuid_identification"
        and ei."third_party_num" = re."third_party_num"
        and ei."invoice_number" = re."invoice_number"
        and ei."invoice_year" = re."invoice_year"
    )
"""
)
