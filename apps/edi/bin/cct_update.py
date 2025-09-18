# pylint: disable=E0401,C0303
"""
FR : Module d'update des cct dans la table edi_import
EN : Module for updating ccts in the edi_import table

Commentaire:

created at: 2022-12-29
created by: Paulo ALVES

modified at: 2022-12-29
modified by: Paulo ALVES
"""
from django.db import connection, transaction

from apps.edi.sql_files.sql_common import BASE_SQL_CCT, SQL_SIGNBOARD


@transaction.atomic
def update_cct_edi_import():
    """Fonction d'update des cct depuis book_supplier_cct"""
    with connection.cursor() as cursor:
        cursor.execute(BASE_SQL_CCT)
        cursor.execute(SQL_SIGNBOARD)
