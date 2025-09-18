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

SQL_DETAILS = sql.SQL(
    """
    select 
        (
            "ii"."libelle" 
            || 
            '<br>' 
            || 
            "ii"."command_reference"
        ) as "personnel", 
        "ii"."personnel_type",
        "ii"."qty",
        "sd"."net_unit_price",
        "sd"."net_amount",
        ("sd"."vat_rate" * 100) as "taux_tva",
        "sd"."vat_amount",
        "sd"."amount_with_vat"
    from "invoices_saleinvoicedetail" "sd"
    join "invoices_invoicecommondetails" as "ii"
    on "ii"."import_uuid_identification" = "sd"."import_uuid_identification" 
    join "book_society" "bs"
    on "bs"."third_party_num" = "ii"."third_party_num" 
    where "uuid_invoice" = %(uuid_invoice)s
    """
)

SQL_RESUME = sql.SQL(
    """    
    select 
        sum("sd"."net_amount") as "net_amount",
        sum("sd"."vat_amount") as "vat_amount",
        sum("sd"."amount_with_vat") as "amount_with_vat"
    from "invoices_saleinvoicedetail" "sd"
    where "uuid_invoice" = %(uuid_invoice)s
    """
)
