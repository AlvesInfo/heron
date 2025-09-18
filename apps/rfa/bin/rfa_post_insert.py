# pylint: disable=E0401,C0303,E1101,R0915,R0914
"""
FR : Module des requêtes sql de post-traitement après génération des RFA
EN : Post-processing sql module after generate RFA

Commentaire:

created at: 2024-08-09
created by: Paulo ALVES

modified at: 2024-08-09
modified by: Paulo ALVES
"""
from typing import AnyStr

from django.db import connection

from apps.rfa.sql_files.sql_rfa import rfa_dict
from apps.edi.bin.edi_post_processing_pool import post_general


def rfa_post_upadte(uuid_identification: AnyStr):
    """
    Mise à jour des champs vides à l'import du fichier BBGR Statment
    :param uuid_identification: uuid_identification
    """
    sql_vat = rfa_dict.get("sql_vat")
    sql_total_amount_by_invoices = rfa_dict.get("sql_total_amount_by_invoices")

    with connection.cursor() as cursor:
        cursor.execute(sql_vat, {"uuid_identification": uuid_identification})
        cursor.execute(sql_total_amount_by_invoices, {"uuid_identification": uuid_identification})
        post_general(uuid_identification, cursor)
