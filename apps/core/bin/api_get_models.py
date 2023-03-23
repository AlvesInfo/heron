# pylint: disable=E0401,C0303,E1101
"""
FR : Module de traitement des nouveaux articles pour dans la table articles avec new_article = true
EN : New article processing module for in articles table with new_article = true

Commentaire:

created at: 2023-03-18
created by: Paulo ALVES

modified at: 2023-03-18
modified by: Paulo ALVES
"""
from typing import AnyStr

from django.db.models import CharField, Value, Case, When, Q, F
from django.db.models.functions import Concat

from apps.accountancy.models import VatSage
from apps.articles.models import Article
from apps.book.models import Society
from apps.centers_clients.models import Maison
from apps.parameters.models import UnitChoices


def get_articles_alls() -> Article.objects:
    """
    Retourne l'ensemble des Articles
    :return: queryset of dict
    """
    queryset = (
        Article.objects.annotate(
            str_search=Concat(
                "third_party_num",
                Value("|"),
                "reference",
                Value("|"),
                "ean_code",
                Value("|"),
                "libelle",
                Value("|"),
                "libelle_heron",
                output_field=CharField(),
            ),
            model=Concat(
                "third_party_num",
                Value(" - "),
                "reference",
                Value(" - "),
                Case(
                    When(
                        Q(libelle_heron__isnull=True) | Q(libelle_heron=""),
                        then="libelle",
                    ),
                    default="libelle_heron",
                ),
            ),
        )
        .values("pk", "model")
    )

    return queryset


def get_articles(str_query: AnyStr) -> Article.objects:
    """
    Recherche par API des Articles
    :param str_query: Texte à rechercher pour l'api dropdown
    :return: queryset of dict
    """
    queryset = get_articles_alls()

    return queryset.filter(str_search__icontains=str_query)[:50]


def get_societies_alls() -> Society.objects:
    """
    Recherche par API des tiers
    :return: queryset of dict
    """
    queryset = (
        Society.objects.annotate(
            str_search=Concat(
                "third_party_num",
                Value("|"),
                "name",
                Value("|"),
                "immeuble",
                Value("|"),
                "adresse",
                Value("|"),
                "ville",
                Value("|"),
                "country__country_name",
                output_field=CharField(),
            ),
            pk=F("third_party_num"),
            model=Concat(
                "third_party_num",
                Value(" - "),
                "name",
                Value(" - "),
                "ville",
                Value(" - "),
                "country__country_name",
                output_field=CharField(),
            ),
        )
        .values("pk", "model")
    )

    return queryset


def get_societies(str_query: AnyStr) -> Society.objects:
    """
    Recherche par API des tiers
    :param str_query: Texte à rechercher pour l'api dropdown
    :return: queryset of dict
    """
    queryset = get_societies_alls()

    return queryset.filter(str_search__icontains=str_query)[:50]


def get_maisons_alls() -> Maison.objects:
    """
    Recherche par API des CCT / Maisons
    :return: queryset of dict
    """
    queryset = (
        Maison.objects.annotate(
            str_search=Concat(
                "cct",
                Value("|"),
                "third_party_num",
                Value("|"),
                "intitule",
                Value("|"),
                "immeuble",
                Value("|"),
                "adresse",
                Value("|"),
                "ville",
                Value("|"),
                "pays__country_name",
                output_field=CharField(),
            ),
            pk=F("cct"),
            model=Concat(
                "cct",
                Value(" - "),
                "intitule",
                Value(" - "),
                "ville",
                output_field=CharField(),
            ),
        )
        .values("pk", "model")
    )

    return queryset


def get_maisons(str_query: AnyStr) -> Maison.objects:
    """
    Recherche par API des CCT / Maisons
    :param str_query: Texte à rechercher pour l'api dropdown
    :return: queryset of dict
    """
    queryset = get_maisons_alls()

    return queryset.filter(str_search__icontains=str_query)[:50]


def get_unity_alls() -> UnitChoices.objects:
    """
    Recherche par API des Unitées
    :return: queryset of dict
    """
    queryset = (
        UnitChoices.objects.annotate(
            str_search=F("unity"),
            pk=F("num"),
            model=F("unity"),
        )
        .values("num", "unity")
    )

    return queryset


def get_unity(str_query: AnyStr) -> UnitChoices.objects:
    """
    Recherche par API des Unitées
    :param str_query: Texte à rechercher pour l'api dropdown
    :return: queryset of dict
    """
    queryset = get_unity_alls()

    return queryset.filter(str_search__icontains=str_query)


def get_vat_alls() -> VatSage.objects:
    """
    Recherche par API des VatSage
    :return: queryset of dict
    """
    queryset = (
        VatSage.objects.annotate(
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
        )
        .values("vat", "vat_regime")
    )

    return queryset


def get_vat(str_query: AnyStr) -> VatSage.objects:
    """
    Recherche par API des VatSage
    :param str_query: Texte à rechercher pour l'api dropdown
    :return: queryset of dict
    """
    queryset = get_vat_alls()

    return queryset.filter(str_search__icontains=str_query)
