# pylint: disable=E0401
"""
Vérification de la présence des Abonnements pour une période donnée
FR : Module de la vérification de la présence des Abonnements pour une période donnée
EN : Module for checking the presence of Subscriptions for a given periode

Commentaire:

created at: 2023-03-04
created by: Paulo ALVES

modified at: 2023-03-04
modified by: Paulo ALVES
"""
import os
import platform
import sys

from typing import AnyStr

from psycopg2 import sql
import django
from django.db import connection

BASE_DIR = r"C:\SitesWeb\heron"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")
django.setup()


def get_have_subscriptions(flow_name: AnyStr, dte_d: AnyStr, dte_f: AnyStr) -> bool:
    """Vérifie si il y a des abonnements existants pour la période
    :param flow_name: flow_name à vérifier
    :param dte_d: Date de début de période au format texte isoformat
    :param dte_f: Date de fin de période au format texte isoformat
    :return:
    """
    with connection.cursor() as cursor:
        sql_subscriptions = sql.SQL(
            """
            ( 
                select  
                    "sbe"."id"
                from "edi_ediimport" "sbe" 
                where "flow_name" = %(flow_name)s
                and "invoice_date" between %(dte_d)s and %(dte_f)s
                limit 1
            )
            union all 
            (
                select 
                    "sbi"."id"
                from "invoices_invoice" "si"
                join "invoices_invoicedetail" "sbi"
                on "si"."uuid_identification"  = "sbi"."uuid_invoice" 
                where "sbi"."flow_name" = %(flow_name)s
                and "si"."invoice_date" between %(dte_d)s and %(dte_f)s
                limit 1
            )
            """
        )
        cursor.execute(sql_subscriptions, {"flow_name": flow_name, "dte_d": dte_d, "dte_f": dte_f})
        test_have_lines_subscriptions = cursor.fetchone()

        if test_have_lines_subscriptions:
            return True

    return False


if __name__ == '__main__':
    print(get_have_subscriptions("ROYALTIES", "2023-01-01", "2023-01-31"))
