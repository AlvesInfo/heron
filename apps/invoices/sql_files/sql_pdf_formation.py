# pylint: disable=E0401
"""
FR : Module des requêtes sql, pour les factures de ventes Formation
EN : Module of sql queries, for sales Formation invoices

Commentaire:

created at: 2023-03-11
created by: Paulo ALVES

modified at: 2023-03-11
modified by: Paulo ALVES
"""
from psycopg2 import sql

SQL_FORMATION = sql.SQL(
    """
    select 
        "ii"."initial_date",
        "ii"."final_date",
        "ii"."libelle" as "formation", 
        "ii"."first_name",
        "ii"."last_name",
        "ii"."heures_formation",
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
