# pylint: disable=E0401,C0303,E1101
"""
FR : Module API d'appelle des dropdown, pour remplissage à l'appel
EN : API module for calling dropdowns, for filling on call

Commentaire:

created at: 2023-08-20
created by: Paulo ALVES

modified at: 2023-08-20
modified by: Paulo ALVES
"""
from typing import AnyStr

from django.db.models import CharField, Value, F
from django.db.models.functions import Concat

from apps.accountancy.models import VatSage


def get_vat_alls() -> VatSage.objects:
    """
    Recherche par API des VatSage
    :return: queryset of dict
    """
    queryset = VatSage.objects.annotate(
        str_search=Concat(
            "vat",
            Value("|"),
            "vat_regime",
            output_field=CharField(),
        ),
        pk=F("vat"),
        model=Concat(
            "vat",
            Value(" - "),
            "vat_regime",
            output_field=CharField(),
        ),
    ).values("pk", "model")

    return queryset


def get_vat(str_query: AnyStr) -> VatSage.objects:
    """
    Recherche par API des VatSage
    :param str_query: Texte à rechercher pour l'api dropdown
    :return: queryset of dict
    """
    queryset = get_vat_alls()

    return queryset.filter(str_search__icontains=str_query)