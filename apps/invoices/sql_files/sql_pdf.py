# pylint: disable=E0401
"""
FR : Module des requêtes sql, pour les factures de ventes
EN : Module of sql queries, for sales invoices

Commentaire:

created at: 2023-03-11
created by: Paulo ALVES

modified at: 2023-03-11
modified by: Paulo ALVES
"""
from psycopg2 import sql

SQL_HEADAER = sql.SQL(
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
