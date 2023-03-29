# pylint: disable=E0401
"""
FR : Module des requêtes sql, pour l'insertion en base des invoices
EN : Module of sql queries, for the insertion in the base of invoices

Commentaire:

created at: 2023-03-11
created by: Paulo ALVES

modified at: 2023-03-11
modified by: Paulo ALVES
"""
from psycopg2 import sql

SQL_INVOICES = sql.SQL(
    """
    insert into invoices_invoice iv
    (
        "created_at", 
        "modified_at", 
        "active", 
        "delete", 
        "export", 
        ""valid"", 
        "final_at", 
        "acquitted", 
        "level_group", 
        "flag_to_active", 
        "flag_to_delete", 
        "flag_to_export", 
        "flag_to_valid", 
        "flag_to_acquitted", 
        "uuid_file", 
        "invoice_number", 
        "invoice_date", 
        "invoice_month", 
        "invoice_year", 
        "invoice_type", 
        "devise", 
        "sale_devise", 
        "sale_invoice_type", 
        "invoice_amount_without_tax", 
        "invoice_amount_tax", 
        "invoice_amount_with_tax", 
        "purchase_invoice", 
        "sale_invoice_amount_without_tax", 
        "sale_invoice_amount_tax", 
        "sale_invoice_amount_with_tax", 
        "sale_invoice", 
        "manual_entry", 
        "uuid_identification", 
        "sale_invoice_number", 
        "sale_invoice_date", 
        "sale_invoice_month", 
        "sale_invoice_year", 
        "sale_invoice_periode", 
        "vat_regime", 
        "big_category", 
        "acquitted_by", 
        "cct", 
        "centers", 
        "created_by", 
        "delete_by", 
        "modified_by", 
        "parties", 
        "third_party_num", 
        "uuid_control", 
        "signboard"
    )
    """
)
