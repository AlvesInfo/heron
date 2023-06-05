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

from django.db import connection
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


def set_exchanges_sales_cosium(sale_month, currency_change):
    """
    Mise à jour des taux de change dans les ventes après mise à jour du taux
    :param sale_month: mois du taux de change
    :param currency_change: monaie du taux de change
    :return:
    """
    sql_update_sales = """
    update "compta_ventescosium" "vc"
    set "taux_change_moyen" = round((1/"req"."rate")::numeric ,5)::numeric,
        "ca_ht_ap_remise_eur" = round(
                                        "ca_ht_ap_remise"
                                        *
                                        round((1/"req"."rate")::numeric ,5)::numeric, 2
                              )::numeric,
        "ca_ht_avt_remise_eur" = round(
                                        "ca_ht_avt_remise"
                                        *
                                        round((1/"req"."rate")::numeric ,5)::numeric, 2
                               )::numeric,
        "pv_brut_unitaire_eur" = round(
                                        "pv_brut_unitaire"
                                        *
                                        round((1/"req"."rate")::numeric ,5)::numeric, 2
                               )::numeric,
        "pv_net_unitaire_eur" = round(
                                        "pv_net_unitaire"
                                        *
                                        round((1/"req"."rate")::numeric ,5)::numeric, 2
                                   )::numeric,
        "px_vente_ttc_eur" = round(
                                    "px_vente_ttc_devise"
                                    *
                                    round((1/"req"."rate")::numeric ,5)::numeric, 2
                                )::numeric,
        "px_vente_ttc_eur_apres_remise" = round(
                                            "px_vente_ttc_devise_apres_remise"
                                            *
                                            round((1/"req"."rate")::numeric ,5)::numeric, 2
                                        )::numeric
    from (
        select 
            "cv"."id", "cc"."currency_iso", "pe"."rate_month", "pe"."rate" 
        from "compta_ventescosium" "cv" 
        join "centers_clients_maison" "ccm" 
        on "cv"."cct_uuid_identification" = "ccm"."uuid_identification" 
        join "countries_country" "cc" 
        on "ccm"."pays" = "cc"."country" 
        join "parameters_exchangerate" "pe" 
        on "cv"."sale_month" = "pe"."rate_month"
        and "cc"."currency_iso" = "pe"."currency_change"
        where "cv"."sale_month" = %(sale_month)s
        and "pe"."currency_change" = %(currency_change)s
    ) req 
    where "vc"."id" = "req"."id"
    """

    with connection.cursor() as cursor:
        print(f"execution : {sale_month} - {currency_change}")
        cursor.execute(
            sql_update_sales, {"sale_month": sale_month, "currency_change": currency_change}
        )
