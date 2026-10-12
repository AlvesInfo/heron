"""FR : Module de recherches et get des articles.

EN : Search and get module for articles.

Commentaire:

created at: 2023-03-24
created by: Paulo ALVES

modified at: 2023-03-24
modified by: Paulo ALVES
"""

from collections.abc import Mapping
from typing import Any

from django.db.models import Case, F, Q, When

from apps.articles.models import Article


def get_articles(articles_pk_list: list) -> dict:
    """Renvoie un dictionnaire des articles recherchés.

    :param articles_pk_list: liste  des articles recherchés
    :return: Article.objects.values.
    """
    articles = (
        Article.objects.filter(pk__in=articles_pk_list)
        .annotate(
            libelle_article=Case(
                When(
                    Q(libelle_heron__isnull=True) | Q(libelle_heron=""),
                    then="libelle",
                ),
                default="libelle_heron",
            ),
        )
        .values(
            "pk",
            "reference",
            "ean_code",
            "libelle_article",
            "famille",
            "axe_bu",
            "axe_prj",
            "axe_pro",
            "axe_pys",
            "axe_rfa",
            "big_category",
            "sub_category",
            "customs_code",
            "item_weight",
        )
        .annotate(libelle=F("libelle_article"), reference_article=F("reference"))
        .values(
            "pk",
            "reference_article",
            "ean_code",
            "libelle",
            "famille",
            "axe_bu",
            "axe_prj",
            "axe_pro",
            "axe_pys",
            "axe_rfa",
            "big_category",
            "sub_category",
            "customs_code",
            "item_weight",
        )
    )

    return {
        row["pk"]: {key: value for key, value in row.items() if key != "pk"} for row in articles
    }


def get_article(article_pk: int) -> Mapping[str, Any] | None:
    """Renvoie un dictionnaire de l'article recherché.

    :param article_pk: id de l'article recherché
    :return: Article.objects.values.
    """
    return (
        Article.objects.filter(pk=article_pk)
        .annotate(
            libelle_article=Case(
                When(
                    Q(libelle_heron__isnull=True) | Q(libelle_heron=""),
                    then="libelle",
                ),
                default="libelle_heron",
            )
        )
        .values(
            "reference",
            "ean_code",
            "libelle_article",
            "famille",
            "axe_bu",
            "axe_prj",
            "axe_pro",
            "axe_pys",
            "axe_rfa",
            "big_category",
            "sub_category",
            "customs_code",
            "item_weight",
            "unit_weight",
        )
        .annotate(libelle=F("libelle_article"), reference_article=F("reference"))
        .values(
            "reference_article",
            "ean_code",
            "libelle",
            "famille",
            "axe_bu",
            "axe_prj",
            "axe_pro",
            "axe_pys",
            "axe_rfa",
            "big_category",
            "sub_category",
            "customs_code",
            "item_weight",
            "unit_weight",
        )
        .first()
    )
