# pylint: disable=E0401
"""
FR : Module des requêtes sql, pour les factures de ventes Publicite
EN : Module of sql queries, for sales Publicity invoices

Commentaire:

created at: 2023-03-16
created by: Paulo ALVES

modified at: 2023-03-16
modified by: Paulo ALVES
"""
from psycopg2 import sql

SQL_HEADER = sql.SQL(
    """
    select 
    "ii"."libelle",
        case 
            when "ii"."unit_weight" = '%%'
            then ("ii"."qty" * 100)::numeric 
            else "ii"."qty" 
        end as "qty" ,
        "ii"."unit_weight",
        "sd"."net_unit_price" as "base",
        case when "sd"."vat_rate" = 0 then "sd"."net_amount" else 0 end as "mont_00",
        case when "sd"."vat_rate" != 0 then "sd"."net_amount" else 0 end as "mont_20",
        "sd"."net_amount",
        "sd"."vat_amount",
        "sd"."amount_with_vat"
    from "invoices_saleinvoicedetail" "sd"
    join "invoices_invoicecommondetails" as "ii"
    on "ii"."import_uuid_identification" = "sd"."import_uuid_identification" 
    join "book_society" "bs"
    on "bs"."third_party_num" = "ii"."third_party_num" 
    where "uuid_invoice" = %(uuid_invoice)s
    order by "ii"."libelle" desc
    """
)

SQL_RESUME_HEADER = sql.SQL(
    """    
    select 
        sum("mont_00") as "net_mont_00",
        sum("mont_20") as "mont_20",
        sum("net_amount") as "net_amount",
        sum("vat_00") as "vat_00",
        sum("vat_20") as "vat_20",
        sum("vat_amount") as "vat_amount",
        sum("ttc_vat_00") as "ttc_vat_00",
        sum("ttc_vat_20") as "ttc_vat_20",
        sum("amount_with_vat") as "amount_with_vat"
    from (
        select 
            case when "sd"."vat_rate" = 0 then "sd"."net_amount" else 0 end as "mont_00",
            case when "sd"."vat_rate" != 0 then "sd"."net_amount" else 0 end as "mont_20",
            "sd"."net_amount",
            case when "sd"."vat_rate" = 0 then "sd"."vat_amount" else 0 end as "vat_00",
            case when "sd"."vat_rate" != 0 then "sd"."vat_amount" else 0 end as "vat_20",
            "sd"."vat_amount",
            case when "sd"."vat_rate" = 0 then "sd"."amount_with_vat" else 0 end as "ttc_vat_00",
            case when "sd"."vat_rate" != 0 then "sd"."amount_with_vat" else 0 end as "ttc_vat_20",
            "sd"."amount_with_vat"
        from "invoices_saleinvoicedetail" "sd"
        join "invoices_invoicecommondetails" as "ii"
        on "ii"."import_uuid_identification" = "sd"."import_uuid_identification" 
        join "book_society" "bs"
        on "bs"."third_party_num" = "ii"."third_party_num" 
        where "uuid_invoice" = %(uuid_invoice)s
    ) "head"
    """
)

