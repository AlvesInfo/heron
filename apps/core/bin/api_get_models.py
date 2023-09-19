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

from apps.accountancy.models import VatSage, AccountSage
from apps.articles.models import Article
from apps.book.models import Society
from apps.centers_clients.models import Maison
from apps.parameters.models import UnitChoices


def get_articles_alls(third_party_num: AnyStr = None) -> Article.objects:
    """
    Retourne l'ensemble des Articles
    :param third_party_num: Tiers X3
    :return: queryset of dict
    """
    queryset = Article.objects.annotate(
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
    ).values("pk", "model")

    if third_party_num is None:
        return queryset

    return queryset.filter(third_party_num=third_party_num)


def get_articles(str_query: AnyStr, third_party_num: AnyStr = None) -> Article.objects:
    """
    Recherche par API des Articles
    :param str_query: Texte à rechercher pour l'api dropdown
    :param third_party_num: Tiers X3 pour filtrer davantage
    :return: queryset of dict
    """
    queryset = get_articles_alls()

    if third_party_num is not None:
        try:
            society = Society.objects.get(third_party_num=third_party_num)

            # Si le tiers n'est pas flagué
            # is_multi_billing (multi - fournisseurs articles) on filtre sur le tiers
            if not society.is_multi_billing:
                return queryset.filter(third_party_num=society, str_search__icontains=str_query)[
                    :50
                ]

        except Society.DoesNotExist:
            pass

    return queryset.filter(str_search__icontains=str_query)[:50]


def get_societies_alls() -> Society.objects:
    """
    Recherche par API des tiers
    :return: queryset of dict
    """
    queryset = Society.objects.annotate(
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
    ).values("pk", "model")

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
    queryset = Maison.objects.annotate(
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
        pk=F("uuid_identification"),
        model=Concat(
            "cct",
            Value(" - "),
            "intitule",
            Value(" - "),
            "adresse",
            Value(" - "),
            "ville",
            output_field=CharField(),
        ),
    ).values("pk", "model")

    return queryset


def get_maisons(str_query: AnyStr) -> Maison.objects:
    """
    Recherche par API des CCT / Maisons
    :param str_query: Texte à rechercher pour l'api dropdown
    :return: queryset of dict
    """
    queryset = get_maisons_alls()

    return queryset.filter(str_search__icontains=str_query)[:50]


def get_maisons_in_use(str_query: AnyStr) -> Maison.objects:
    """
    Recherche par API des CCT / Maisons des maisons non fermées ou plus utilisées
    :param str_query: Texte à rechercher pour l'api dropdown
    :return: queryset of dict
    """
    queryset = get_maisons_alls()

    return queryset.filter(closing_date__isnull=True, str_search__icontains=str_query)[:50]


def get_cct_in_use_active(str_query: AnyStr) -> Maison.objects:
    """
    Recherche par API des CCT / Maisons des maisons non fermées ou inactives
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
                Value(" - "),
                "adresse",
                Value(" - "),
                "ville",
                output_field=CharField(),
            ),
        )
        .values("pk", "model")
        .filter(
            closing_date__isnull=True,

            str_search__icontains=str_query)
    )

    return queryset[:50]


def get_unity_alls() -> UnitChoices.objects:
    """
    Recherche par API des Unitées
    :return: queryset of dict
    """
    queryset = UnitChoices.objects.annotate(
        str_search=F("unity"),
        pk=F("num"),
        model=F("unity"),
    ).values("num", "unity")

    return queryset


def get_unity(str_query: AnyStr) -> UnitChoices.objects:
    """
    Recherche par API des Unitées
    :param str_query: Texte à rechercher pour l'api dropdown
    :return: queryset of dict
    """
    queryset = get_unity_alls()

    return queryset.filter(str_search__icontains=str_query)


def get_accounts_alls() -> AccountSage.objects:
    """
    Recherche par API des Comptes Sage X3
    :return: queryset of dict
    """
    queryset = AccountSage.objects.annotate(
        str_search=Concat(
            "account",
            Value(" - "),
            "code_plan_sage",
            output_field=CharField(),
        ),
        pk=F("uuid_identification"),
        model=Concat(
            "account",
            Value(" - "),
            "code_plan_sage",
            output_field=CharField(),
        ),
    ).values("pk", "model")

    return queryset


def get_account(str_query: AnyStr) -> AccountSage.objects:
    """
    Recherche par API des Comptes Sage X3
    :param str_query: Texte à rechercher pour l'api dropdown
    :return: queryset of dict
    """
    queryset = get_accounts_alls()

    return queryset.filter(str_search__icontains=str_query)
