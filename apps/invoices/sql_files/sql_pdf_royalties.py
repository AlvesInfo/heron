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

SQL_ROYALTIES = sql.SQL(
    """
    select 
    "ii"."libelle",
        case 
            when "ii"."unit_weight" = '%'
            then ("ii"."qty" * 100)::numeric 
            else "ii"."qty" 
        end as "qty" ,
        "ii"."unit_weight",
        "sd"."net_unit_price" as "base",
        case when "sd"."vat_rate" = 0 then "sd"."net_amount" else 0 end as "mont_00",
        case when "sd"."vat_rate" != 0 then "sd"."net_amount" else 0 end as "mont_20",
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

