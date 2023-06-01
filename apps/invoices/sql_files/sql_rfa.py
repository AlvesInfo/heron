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
        "axe_prj", 
        "axe_rfa",
        "grouping_goods",
        sum("net_amount_00") as "net_amount_00",
        sum("net_amount_01") as "net_amount_01",
        sum("net_amount_02") as "net_amount_02",
        sum("net_amount") as "net_amount"
    from (
        select 
            "is2"."axe_prj",
            "is2"."axe_rfa", 
            "grouping_goods", 
            case when "vat" not in ('001', '002') then "net_amount" else 0 end as "net_amount_00",
            case when "vat" = '002' then "net_amount" else 0 end as "net_amount_01",
            case when "vat" = '001' then "net_amount" else 0 end as "net_amount_02",
            "net_amount"
        from "invoices_saleinvoicedetail" "is2" 
        join "invoices_invoicecommondetails" "ii"
        on "ii"."import_uuid_identification" = "is2"."import_uuid_identification"
        where "uuid_invoice" = %(uuid_invoice)s
    ) "head"
    group by 
        "axe_prj",
        "axe_rfa", 
        "grouping_goods" 
    order by "axe_prj",
             "grouping_goods"
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
