# pylint: disable=E0401,C0303,E1101,R0914,R1735,R0915,W0150,W0718
"""
FR : Module de traitement des utilitaires pour les éléemnts issus de Sage
EN : Utility processing module for items from Sage

Commentaire:

created at: 2023-03-18
created by: Paulo ALVES

modified at: 2023-03-25
modified by: Paulo ALVES
"""
from typing import AnyStr

from django.db import connection


def get_dict_vat_rates(invoice_date: AnyStr):
    """
    Retourne un dictionnaire des taux de tva à la date de la facture
    :param invoice_date: date de la facture au format isoformat
    :return: vat_rat dict
    """

    with connection.cursor() as cursor:
        sql_vat_rate = """
        select distinct
            "vtr"."vat", "vtr"."vat_regime", ("vtr"."rate" / 100)::numeric as "vat_rate"
        from "accountancy_vatratsage" "vtr"
        join (
            select
                max("vat_start_date") as "vat_start_date",
                "vat",
                "vat_regime"
            from "accountancy_vatratsage"
            where "vat_start_date" <= %(invoice_date)s
            group by "vat", "vat_regime"
        ) "vd"
        on "vtr"."vat" = "vd"."vat"
        and "vtr"."vat_start_date" = "vd"."vat_start_date"
        """
        cursor.execute(sql_vat_rate, {"invoice_date": invoice_date})

        return {row[0]: row[1:] for row in cursor.fetchall()}


def get_vat_rate(invoice_date: AnyStr, vat: AnyStr):
    """
    Retourne le taux de tva à la date de la facture, et le régime
    :param invoice_date: date de la facture au format isoformat
    :param vat: tva X3
    :return: vat_regime, vat_rate
    >>> from apps.core.functions.functions_setups import connection
    >>> get_vat_rate("2023-01-01", "001")
    ('FRA', Decimal('0.20000'))
    >>> get_vat_rate("2023-01-01", "002")
    ('FRA', Decimal('0.05500'))
    >>> get_vat_rate("2022-01-01", "001")
    ('FRA', Decimal('0.19600'))
    """

    with connection.cursor() as cursor:
        sql_vat_rate = """
        select distinct
            "vtr"."vat_regime", round(("vtr"."rate" / 100)::numeric, 5) as "vat_rate"
        from "accountancy_vatratsage" "vtr"
        join (
            select
                max("vat_start_date") as "vat_start_date",
                "vat",
                "vat_regime"
            from "accountancy_vatratsage"
            where "vat_start_date" <= %(invoice_date)s
            group by "vat", "vat_regime"
        ) "vd"
        on "vtr"."vat" = "vd"."vat"
        and "vtr"."vat_start_date" = "vd"."vat_start_date"
        and "vtr"."vat" = %(vat)s
        """
        cursor.execute(sql_vat_rate, {"invoice_date": invoice_date, "vat": vat})

        return cursor.fetchone()
