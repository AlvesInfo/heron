# pylint: disable=E0401,E1101,C0303,R0913,W0613,R0914,W0611,C0413
"""
FR : Module de calcul des échéances et fonction des modes de règlements
EN : Module for calculating deadlines and function of payment methods
Commentaire:

created at: 2023-06-21
created by: Paulo ALVES

modified at: 2023-06-21
modified by: Paulo ALVES
"""
import os
import platform
import sys
from typing import Tuple
from functools import lru_cache
from uuid import UUID
import datetime

import pendulum
import django

BASE_DIR = r"C:\SitesWeb\heron"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")

django.setup()

from apps.accountancy.models import PaymentCondition


@lru_cache(maxsize=256)
def get_payment_method_elements(uuid_payment_method: UUID) -> Tuple:
    """
    Fonction qui renvoie les éléments de calculs des échéances en fonction du mode de règlement
    :param uuid_payment_method: auuid sage du Mode de règlement
    :return:
    """
    end_month, offset_days, offset_month = None, None, None

    try:
        end_month, offset_days, offset_month = PaymentCondition.objects.values_list(
            "end_month", "offset_days", "offset_month"
        ).get(auuid=uuid_payment_method)

        end_month = int(end_month)

    except PaymentCondition.DoesNotExist:
        return end_month, offset_days, offset_month

    return end_month, offset_days, offset_month


def get_due_date(invoice_date, uuid_payment_method: UUID) -> datetime.date.isoformat:
    """
    Renvoi la date d'échéance du paiement de la facture
    :param invoice_date: date de la facture
    :param uuid_payment_method: auuid sage du Mode de règlement
    :return:
    """
    end_month, offset_days, offset_month = get_payment_method_elements(uuid_payment_method)
    due_date = pendulum.parse(invoice_date)

    if end_month is None:
        return due_date.add(months=offset_month).last_of("month")

    # Si end_month == 1 (Non) -> date_facture : 16/10/2023, départ échéance : 16/10/2023

    # Si end_month == 2 (fin de mois après)->date_facture : 16/10/2023, départ échéance : 31/10/2023
    if end_month == 2:
        due_date = due_date.last_of("month")

    # Si end_month == 3 (fin de mois avant)->date_facture : 16/10/2023, départ échéance : 30/09/2023
    if end_month == 3:
        due_date = due_date.subtract(months=1).last_of("month")

    if offset_month:
        due_date = due_date.add(months=offset_month)

    if offset_days:
        due_date = due_date.add(days=offset_days)

    return due_date.to_date_string()
