# pylint: disable=E0401
"""
FR : Module des taux de change
EN : Exhange rates module

Commentaire:

created at: 2023-06-23
created by: Paulo ALVES

modified at: 2023-06-23
modified by: Paulo ALVES
"""
from typing import AnyStr

from django.db.models import Exists, OuterRef, Count, F

from apps.compta.models import VentesCosium
from apps.countries.models import Currency
from apps.parameters.models import ExchangeRate


def set_base_exchange_rate(month: AnyStr) -> None:
    """
    Crééer des lignes de taux de change par défaut pour les mois demander,
    sur la base des ventes Cosium
    :param month: mois des ventes
    :return: None
    """
    sales_currencies = (
        VentesCosium.objects.exclude(cct_uuid_identification__isnull=True)
        .annotate(
            rate_exists=Exists(
                ExchangeRate.objects.filter(
                    currency_change=OuterRef("cct_uuid_identification__pays__currency_iso")
                )
            )
        )
        .annotate(currency=F("cct_uuid_identification__pays__currency_iso"))
        .values("currency")
        .filter(sale_month=month, rate_exists=False)
        .annotate(dcount=Count("currency"))
        .values_list("currency", flat=True)
    )

    for currency in sales_currencies:
        try:
            currency_change = Currency.objects.get(code=currency)
            ExchangeRate.objects.get_or_create(
                currency_change=currency_change,
                rate_month=month,
                rate=1 if currency == "EUR" else 0,
            )
        except Currency.DoesNotExist:
            pass
