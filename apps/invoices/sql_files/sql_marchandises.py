# pylint: disable=E0401
"""
FR : Module des requêtes sql, pour les factures de ventes Marchandises
EN : Module of sql queries, for sales Marchandises invoices

Commentaire:

created at: 2023-03-11
created by: Paulo ALVES

modified at: 2023-03-11
modified by: Paulo ALVES
"""
from psycopg2 import sql

SQL_HEADER = sql.SQL(
    """
    select 
        "base", 
        "grouping_goods",
        sum("net_amount_00") as "net_amount_00",
        sum("net_amount_01") as "net_amount_01",
        sum("net_amount_02") as "net_amount_02",
        sum("net_amount") as "net_amount"
    from (
        select 
            "ranking",
            "base", 
            "grouping_goods", 
            case when "vat" not in ('001', '002') then "net_amount" else 0 end as "net_amount_00",
            case when "vat" = '002' then "net_amount" else 0 end as "net_amount_01",
            case when "vat" = '001' then "net_amount" else 0 end as "net_amount_02",
            "net_amount"
        from "invoices_saleinvoicedetail" "is2" 
        where "uuid_invoice" = %(uuid_invoice)s
    ) "head"
    group by 
        "ranking",
        "base", 
        "grouping_goods" 
    order by "ranking"
    """
)

SQL_RESUME_HEADER = sql.SQL(
    """
    select 
        sum("net_amount_00") as "net_amount_00",
        sum("vat_amount_00") as "vat_amount_00",
        sum("ttc_amount_00") as "ttc_amount_00",
        sum("net_amount_01") as "net_amount_01",
        sum("vat_amount_01") as "vat_amount_01",
        sum("ttc_amount_01") as "ttc_amount_01",
        sum("net_amount_02") as "net_amount_02",
        sum("vat_amount_02") as "vat_amount_02",
        sum("ttc_amount_02") as "ttc_amount_02",
        sum("net_amount") as "net_amount",
        sum("vat_amount") as "vat_amount",
        sum("amount_with_vat") as "amount_with_vat"
    from (
        select 
            case when "vat" not in ('001', '002') then "net_amount" else 0 end as "net_amount_00",
            case when "vat" not in ('001', '002') then "vat_amount" else 0 end as "vat_amount_00",
            case 
                when "vat" not in ('001', '002') 
                then "amount_with_vat" 
                else 0 
            end as "ttc_amount_00",
            case when "vat" = '002' then "net_amount" else 0 end as "net_amount_01",
            case when "vat" = '002' then "vat_amount" else 0 end as "vat_amount_01",
            case when "vat" = '002' then "amount_with_vat" else 0 end as "ttc_amount_01",
            case when "vat" = '001' then "net_amount" else 0 end as "net_amount_02",
            case when "vat" = '001' then "vat_amount" else 0 end as "vat_amount_02",
            case when "vat" = '001' then "amount_with_vat" else 0 end as "ttc_amount_02",
            "net_amount",
            "vat_amount",
            "amount_with_vat" 
        from "invoices_saleinvoicedetail" 
        where "uuid_invoice" = %(uuid_invoice)s
    ) "head"
    """
)

SQL_RESUME_SUPPLIER = sql.SQL(
    """
    select 
        "bs"."name" as "supplier_name",
        sum("sd"."net_amount") as "net_amount",
        sum("sd"."vat_amount") as "vat_amount",
        sum("sd"."amount_with_vat") as "amount_with_vat"
    from "invoices_saleinvoicedetail" "sd"
    join "invoices_invoicecommondetails" as "ii"
    on "ii"."import_uuid_identification" = "sd"."import_uuid_identification" 
    join "book_society" "bs"
    on "bs"."third_party_num" = "ii"."third_party_num" 
    where "uuid_invoice" = %(uuid_invoice)s
    group by "bs"."name"
    order by "bs"."name"
    """
)

SQL_DETAILS = sql.SQL(
    """
    with details as (
        select 
            "bs"."name" as "supplier_name",
            "ii"."invoice_number",
            "ii"."invoice_date",
            case 
                when "ed"."column_name" = 'MONTURES OPTIQUES' 
                then "sd"."net_amount" 
                else 0 
            end as "MO",
            case 
                when "ed"."column_name" = 'MONTURES SOLAIRES' 
                then "sd"."net_amount" 
                else 0 
            end as "MS",
            case 
                when "ed"."column_name" = 'VERRES' 
                then "sd"."net_amount" 
                else 0 
            end as "VE",
            case 
                when "ed"."column_name" = 'CONTACTO - SOLUTIONS' 
                then "sd"."net_amount" 
                else 0 
            end as "COT",
            case 
                when "ed"."column_name" = 'AIDES AUDITIVES' 
                then "sd"."net_amount" 
                else 0 
            end as "AU",
            case 
                when "ed"."column_name" = 'PILES' 
                then "sd"."net_amount" 
                else 0 
            end as "PI",
            case 
                when "ed"."column_name" = 'ACCESSOIRES AUDIO' 
                then "sd"."net_amount" 
                else 0 
            end as "AC",
            case 
                when "ed"."column_name" = 'ACCESSOIRES OPTIQUE' 
                then "sd"."net_amount" 
                else 0 
            end as "AO",
            case 
                when "ed"."column_name" = 'CONSOMABLES' 
                then "sd"."net_amount" 
                else 0 
            end as "CO",
            case 
                when "ed"."column_name" = 'PORT ET EMBALLAGE' 
                then "sd"."net_amount" 
                else 0 
            end as "PO",
            case 
                when "ed"."column_name" = 'DIVERS' 
                then "sd"."net_amount" 
                else 0 
            end as "DI",
            "sd"."net_amount",
            "sd"."amount_with_vat"
        from "invoices_saleinvoicedetail" "sd"
        join "invoices_invoicecommondetails" as "ii"
        on "ii"."import_uuid_identification" = "sd"."import_uuid_identification" 
        join "book_society" "bs"
        on "bs"."third_party_num" = "ii"."third_party_num" 
        join (
            select 
                "ass"."section" as "axe_pro", 
                "ad"."column_name"
            from "accountancy_sectionsage" "ass"
            join "invoices_axesdetails" "ad"
            on "ad"."axe_pro" = "ass"."uuid_identification" 
        ) "ed"
        on "ed"."axe_pro" = "sd"."axe_pro"
        where "uuid_invoice" = %(uuid_invoice)s
    )
    select 
        "supplier_name",
        "invoice_number",
        "invoice_date",
        sum("MO") as "MO",
        sum("MS") as "MS",
        sum("VE") as "VE",
        sum("COT") as "COT",
        sum("AU") as "AU",
        sum("PI") as "PI",
        sum("AC") as "AC",
        sum("AO") as "AO",
        sum("CO") as "CO",
        sum("PO") as "PO",
        sum("DI") as "DI",
        sum("net_amount") as "total_ht",
        sum("amount_with_vat") as "total_ttc"
    from "details"
    group by "supplier_name",
             "invoice_number",
             "invoice_date"
    order by "supplier_name",
             "invoice_date",
             "invoice_number"
    """
)

SQL_SUB_DETAILS = sql.SQL(
    """
    select 
        "bs"."name" as "supplier_name",
        "ii"."invoice_number",
        "ii"."invoice_date",
        "ii"."delivery_number",
        "ii"."delivery_date",
        case 
            when "sd"."grouping_goods" = 'MONTURES SOLAIRES' then 'MONT. SOL.'
            when "sd"."grouping_goods" = 'MONTURES OPTIQUES' then 'MONT. OPT.'
            else "sd"."grouping_goods"
        end as "grouping_goods",
        "ii"."reference_article" || ' - ' || "ii"."libelle" as "article",
        "ii"."qty",
        "sd"."net_unit_price",
        "sd"."net_amount",
        "ii"."client_name",
        "ii"."serial_number" 
    from "invoices_saleinvoicedetail" "sd"
    join "invoices_invoicecommondetails" as "ii"
    on "ii"."import_uuid_identification" = "sd"."import_uuid_identification" 
    join "book_society" "bs"
    on "bs"."third_party_num" = "ii"."third_party_num" 
    where "uuid_invoice" = %(uuid_invoice)s
    order by "bs"."name",
             "ii"."invoice_number",
             "ii"."invoice_date",
             "ii"."delivery_number",
             "ii"."delivery_date",
             "ii"."id"
    """
)
