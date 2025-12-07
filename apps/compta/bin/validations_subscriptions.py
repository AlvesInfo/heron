# pylint: disable=E0401,C0303
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

import django

BASE_DIR = r"C:\SitesWeb\heron"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")

django.setup()

from psycopg2 import sql
from django.db import connection


def get_have_subscriptions(flow_name: AnyStr, dte_d: AnyStr, dte_f: AnyStr) -> bool:
    """Vérifie s'il y a des abonnements existants pour la période
    :param flow_name: flow_name à vérifier
    :param dte_d: Date de début de période au format texte isoformat
    :param dte_f: Date de fin de période au format texte isoformat
    :return:
    """
    with connection.cursor() as cursor:
        sql_subscriptions = sql.SQL(
            """
            SELECT EXISTS (
                SELECT 1 FROM edi_ediimport
                WHERE flow_name = %(flow_name)s
                AND invoice_date BETWEEN %(dte_d)s AND %(dte_f)s
            ) 
            OR EXISTS (
                SELECT 1 
                FROM invoices_invoicedetail sbi
                JOIN invoices_invoice si ON si.uuid_identification = sbi.uuid_invoice
                WHERE sbi.flow_name = %(flow_name)s
                AND si.invoice_date BETWEEN %(dte_d)s AND %(dte_f)s
            ) AS data_exists;
            """
        )
        cursor.execute(sql_subscriptions, {"flow_name": flow_name, "dte_d": dte_d, "dte_f": dte_f})

        return cursor.fetchone()[0]


def get_missing_cosium_familly(dte_d: AnyStr, dte_f: AnyStr) -> AnyStr:
    """Vérification qu'il ne manque pas de traductions pour les familles Cosium des Ventes Cosium,
    dans la table des statistiques book_supplierfamilyaxes et la stat_name 'COSI001'
    :param dte_d: Date de début de période au format texte isoformat
    :param dte_f: Date de fin de période au format texte isoformat
    :return: texte du message en cas de manquants
    """

    with connection.cursor() as cursor:
        sql_subscriptions = sql.SQL(
            """
            select 
                famille_cosium
            from compta_ventescosium cv 
            left join (
                select 
                    regex_match, axe_pro
                from book_supplierfamilyaxes 
                where stat_name = 'COSI001'
            ) bs 
            on cv.famille_cosium = bs.regex_match
            where date_vente between %(dte_d)s and %(dte_f)s
            group by 	
                famille_cosium,
                rayon_cosium,
                bs.axe_pro
            having bs.axe_pro isnull
            """
        )
        cursor.execute(sql_subscriptions, {"dte_d": dte_d, "dte_f": dte_f})
        test_missing_cosium_familly = cursor.fetchall()

        if test_missing_cosium_familly:
            text_error = (
                "Il manque des familles Cosium : \n    "
                + ", ".join([famille[0] for famille in test_missing_cosium_familly])
                + ",\nà compléter (menu) : Paramétrage - (TIERS) Familles/Axes"
            )

            return text_error

    return ""


def get_ca_exists(dte_d: AnyStr, dte_f: AnyStr) -> bool:
    """Vérifie si le CA à été généré pour la période
    :param dte_d: Date de début de période au format texte isoformat
    :param dte_f: Date de fin de période au format texte isoformat
    :return: bool
    """
    with connection.cursor() as cursor:
        sql_ca_client = sql.SQL(
            """
            select 
                1 as exist
            from compta_ventescosium cv 
            where cv.date_vente between '2023-01-01' and '2023-01-31'
            limit 1
            """
        )
        cursor.execute(sql_ca_client, {"dte_d": dte_d, "dte_f": dte_f})
        test_ca_exists = cursor.fetchone()

        if test_ca_exists:
            return True

    return False


if __name__ == "__main__":
    print("subscriptions : ", get_have_subscriptions("ROYALTIES", "2023-01-01", "2023-01-31"))
    print("get_missing_cosium_familly : ", get_missing_cosium_familly("2023-01-01", "2023-01-31"))
    print("get_ca_exists : ", get_ca_exists("2023-01-01", "2023-01-31"))
