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

SQL_SALES_PRICES = sql.SQL(
    # insertion des prix de ventes
    """
    """
)

SQL_INVOICES = sql.SQL(
    # Insertion des entêtes de factures
    """
    insert into invoices_invoice iv
    (

    )
    """
)
