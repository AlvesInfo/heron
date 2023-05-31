# pylint: disable=W0702,W1203,E0401,E1101
"""Module de stockage des querysets

Commentaire:

created at: 2022-05-29
created by: Paulo ALVES

modified at: 2022-05-29
modified by: Paulo ALVES
"""
from django.db.models import Max, Value, CharField, Exists, OuterRef, Count, Case, When, Q
from django.db.models.functions import Coalesce, Cast

from apps.articles.models import Article, ArticleAccount
from apps.edi.models import EdiImport
from apps.centers_purchasing.models import AccountsAxeProCategory


articles_without_account_queryset = (
    EdiImport.objects.annotate(
        supplierm=Max("supplier"),
        libellem=Max("libelle"),
        sub_categoryc=Coalesce(Cast("sub_category", output_field=CharField()), Value("")),
    )
    .annotate(
        without=Exists(
            AccountsAxeProCategory.objects.annotate(
                sub_categoryc=Coalesce(Cast("sub_category", output_field=CharField()), Value("")),
            ).filter(
                child_center=OuterRef("code_center"),
                axe_pro=OuterRef("axe_pro"),
                big_category=OuterRef("big_category"),
                sub_categoryc=OuterRef("sub_categoryc"),
                vat=OuterRef("vat"),
            )
        ),
        article=Article.objects.filter(
            third_party_num=OuterRef("third_party_num"),
            reference=OuterRef("reference_article"),
        ).values("pk"),
    )
    .annotate()
    .values(
        "code_center",
        "third_party_num",
        "supplierm",
        "reference_article",
        "libellem",
        "axe_pro__section",
        "big_category__name",
        "sub_category__name",
        "vat",
        "article",
    )
    .exclude(without=True)
    .annotate(Count("id"))
    .order_by(
        "code_center",
        "third_party_num",
        "supplierm",
        "reference_article",
        "big_category__name",
        "vat",
    )
)


articles_with_account_queryset = (
    ArticleAccount.objects.annotate(
        sub_categoryc=Coalesce(Cast("article__sub_category", output_field=CharField()), Value("")),
        libelle_article=Case(
            When(
                Q(article__libelle_heron__isnull=True) | Q(article__libelle_heron=""),
                then="article__libelle",
            ),
            default="article__libelle_heron",
        ),
    )
    .values(
        "pk",
        "child_center__code",
        "article__third_party_num",
        "article__third_party_num__short_name",
        "article__reference",
        "libelle_article",
        "article__axe_pro__section",
        "article__big_category__name",
        "sub_categoryc",
        "vat",
        "purchase_account",
        "sale_account",
    )
    .order_by(
        "child_center__code",
        "article__third_party_num",
        "article__third_party_num__short_name",
        "article__reference",
        "article__big_category__name",
        "vat",
    )
)
