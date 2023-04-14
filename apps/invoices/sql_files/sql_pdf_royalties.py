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
        "bs"."name" as "supplier_name",
        "ii"."invoice_number",
        "ii"."invoice_date",
        "ii"."delivery_number",
        "ii"."delivery_date",
        "sd"."grouping_goods",
        "ii"."reference_article",
        "ii"."libelle",
        "ii"."qty",
        "sd"."net_unit_price",
        "sd"."net_amount",
        "sd"."amount_with_vat"
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

