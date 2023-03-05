# pylint: disable=E0401,C0303
"""
Génération du chiffre d'affaires par clients et par AXE_PRO, issus des ventes Cosium
FR : Module de génération du chiffre d'affaire par clients, issus des ventes Cosium
EN : Module for generating turnover by customers, from Cosium sales

Commentaire:

created at: 2023-03-04
created by: Paulo ALVES

modified at: 2023-03-04
modified by: Paulo ALVES
"""
from uuid import UUID
from typing import AnyStr

from psycopg2 import sql
from django.db import connection


def delete_ca(dte_d: AnyStr, dte_f: AnyStr):
    """Suppression du CA Client pour une période donnée
    :param dte_d: Date de début de période au format texte isoformat
    :param dte_f: Date de fin de période au format texte isoformat
    :return:
    """
    with connection.cursor() as cursor:
        sql_delete = sql.SQL(
            """
            delete from "compta_caclients" 
            where "date_ca" between %(dte_d)s and %(dte_f)s 
            """
        )
        cursor.execute(sql_delete, {"dte_d": dte_d, "dte_f": dte_f})


def set_ca(dte_d: AnyStr, dte_f: AnyStr, user_uuid: UUID):
    """Génération du chiffre d'affaires par clients et par AXE_PRO, issus des ventes Cosium
    :param dte_d: Date de début de période au format texte isoformat
    :param dte_f: Date de fin de période au format texte isoformat
    :param user_uuid: Utilisateur lançant la génération
    :return:
    """
    with connection.cursor() as cursor:

        sql_insert_statment = sql.SQL(
            """
            insert into "compta_caclients" 
            (
                "created_at",
                "modified_at",
                "active",
                "delete",
                "export",
                "valid",
                "acquitted",
                "flag_to_active",
                "flag_to_delete",
                "flag_to_export",
                "flag_to_valid",
                "flag_to_acquitted",
                "date_ca",
                "code_maison",
                "code_cosium",
                "cct_uuid_identification",
                "famille_cosium",
                "axe_pro",
                "ca_ht_eur",
                "ca_ht_devise",
                "created_by"
            )
            select 
                now() as "created_at",
                now() as "modified_at",
                false as "active",
                false as "delete",
                false as "export",
                false as "valid",
                false as "acquitted",
                false as "flag_to_active",
                false as "flag_to_delete",
                false as "flag_to_export",
                false as "flag_to_valid",
                false as "flag_to_acquitted",
                %(dte_f)s as "date_ca",
                "code_maison",
                "code_cosium",
                "cct_uuid_identification",
                string_agg(
                    distinct "famille_cosium", '|' order by "famille_cosium"
                ) as "famille_cosium",
                "bs"."axe_pro" as "axe_pro",
                sum("ca_ht_ap_remise_eur")::numeric as "ca_ht_eur",
                sum("ca_ht_ap_remise")::numeric as "ca_ht_devise",
                %(user)s as "created_by"
            from "compta_ventescosium" "cv" 
            left join "book_supplierfamilyaxes" "bs" 
            on "cv"."famille_cosium" = "bs"."regex_match" 
            where "cv"."date_vente" between %(dte_d)s and %(dte_f)s
            group by 	
                "code_maison",
                "code_cosium",
                "cct_uuid_identification",
                "bs"."axe_pro"
            order by 
                "code_maison",
                "bs"."axe_pro"
            on conflict do nothing
            """
        )
        cursor.execute(
            sql_insert_statment, {"dte_d": dte_d, "dte_f": dte_f, "user": user_uuid}
        )
