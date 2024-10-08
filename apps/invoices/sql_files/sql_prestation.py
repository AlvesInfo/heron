# pylint: disable=E0401
"""
FR : Module des requêtes sql, pour les factures de ventes Prestation
EN : Module of sql queries, for sales Prestation invoices

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
        "sd"."sub_category", 
        "ii"."supplier_initial_libelle" as "libelle",
        case when "sd"."vat_rate" = 0 then "sd"."net_amount" else 0 end as "mont_00",
        case when "sd"."vat_rate" = 0.055 then "sd"."net_amount" else 0 end as "mont_05",
        case when "sd"."vat_rate" = 0.2 then "sd"."net_amount" else 0 end as "mont_20",
        "sd"."net_amount",
        "sd"."vat_amount",
        "sd"."amount_with_vat"
    from "invoices_saleinvoicedetail" "sd"
    join "invoices_invoicecommondetails" as "ii"
    on "ii"."import_uuid_identification" = "sd"."import_uuid_identification" 
    join "book_society" "bs"
    on "bs"."third_party_num" = "ii"."third_party_num" 
    where "uuid_invoice" = %(uuid_invoice)s
    order by "sd"."sub_category", "ii"."libelle" desc
    """
)

SQL_RESUME_HEADER = sql.SQL(
    """    
    select 
        sum("mont_00") as "net_mont_00",
        sum("mont_05") as "net_mont_05",
        sum("mont_20") as "net_mont_20",
        sum("net_amount") as "net_amount",
        sum("vat_00") as "vat_00",
        sum("vat_05") as "vat_05",
        sum("vat_20") as "vat_20",
        sum("vat_amount") as "vat_amount",
        sum("ttc_vat_00") as "ttc_vat_00",
        sum("ttc_vat_05") as "ttc_vat_05",
        sum("ttc_vat_20") as "ttc_vat_20",
        sum("amount_with_vat") as "amount_with_vat"
    from (
        select 
            case when "sd"."vat_rate" = 0 then "sd"."net_amount" else 0 end as "mont_00",
            case when "sd"."vat_rate" = 0.055 then "sd"."net_amount" else 0 end as "mont_05",
            case when "sd"."vat_rate" = 0.2 then "sd"."net_amount" else 0 end as "mont_20",
            "sd"."net_amount",
            case when "sd"."vat_rate" = 0 then "sd"."vat_amount" else 0 end as "vat_00",
            case when "sd"."vat_rate" = 0.055 then "sd"."vat_amount" else 0 end as "vat_05",
            case when "sd"."vat_rate" = 0.2 then "sd"."vat_amount" else 0 end as "vat_20",
            "sd"."vat_amount",
            case when "sd"."vat_rate" = 0 then "sd"."amount_with_vat" else 0 end as "ttc_vat_00",
            case when "sd"."vat_rate" = 0.055 then "sd"."amount_with_vat" else 0 end as "ttc_vat_05",
            case when "sd"."vat_rate" = 0.2 then "sd"."amount_with_vat" else 0 end as "ttc_vat_20",
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

