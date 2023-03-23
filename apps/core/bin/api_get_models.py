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
from typing import AnyStr, Generator

from django.db.models import CharField, Value, Case, When, Q, F
from django.db.models.functions import Concat

from apps.articles.models import Article
from apps.book.models import Society
from apps.centers_clients.models import Maison


def get_articles(str_query: AnyStr) -> Generator:
    """
    Recherche par API des Articles
    :param str_query: Texte à rechercher pour l'api dropdown
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
        .filter(str_search__icontains=str_query)[:50]
    )

    return queryset


def get_societies(str_query: AnyStr) -> Generator:
    """
    Recherche par API des tiers
    :param str_query: Texte à rechercher pour l'api dropdown
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
        .filter(str_search__icontains=str_query)[:50]
    )

    return queryset


def get_maisons(str_query: AnyStr) -> Generator:
    """
    Recherche par API des CCT / Maisons
    :param str_query: Texte à rechercher pour l'api dropdown
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
                output_field=CharField(),
            ),
        )
        .values("pk", "model")
        .filter(str_search__icontains=str_query)[:50]
    )

    return queryset
