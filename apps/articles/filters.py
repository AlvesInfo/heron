# pylint: disable=E0401,R0903
"""
Filtres pour des recherches dans les views
"""
from django import forms
from django.db.models import Max, Value, CharField, Exists, OuterRef, Count, Case, When, Q, F
import django_filters

from apps.articles.models import Article, ArticleAccount
from apps.book.models import Society


class ArticleFilter(django_filters.FilterSet):
    """Filtre des articles"""

    third_party_num = django_filters.MultipleChoiceFilter(
        choices=[(None, "----")]
        + [
            (row.get("third_party_num"), f'{row.get("third_party_num")} - {row.get("name")}')
            for row in (
                Society.objects.annotate(
                    in_articles=Exists(
                        Article.objects.values("third_party_num__third_party_num")
                        .annotate(nbre=Count("third_party_num__third_party_num"))
                        .values("third_party_num__third_party_num")
                        .filter(third_party_num__third_party_num=OuterRef("third_party_num"))
                    )
                )
                .exclude(in_articles=False)
                .values("third_party_num", "name")
            )
        ],
        widget=forms.Select(attrs={"class": "ui fluid search dropdown"}),
    )

    class Meta:
        """class Meta django"""

        model = Article
        fields = {
            "third_party_num": ["exact"],
            "reference": ["icontains"],
            "libelle": ["icontains"],
            "libelle_heron": ["icontains"],
            "big_category": ["exact"],
            "sub_category": ["exact"],
        }


class ArticleAccountFilter(django_filters.FilterSet):
    """Filtre des articles / comptes x3"""

    class Meta:
        """class Meta django"""

        model = ArticleAccount
        fields = ["child_center"]
        # fields = {
        #     "third_party_num": ["exact"],
        #     "reference": ["exact", "icontains"],
        #     "libelle": ["exact", "icontains"],
        #     "libelle_heron": ["exact", "icontains"],
        #     "big_category": ["exact"],
        #     "sub_category": ["exact"],
        #     "axe_pro_supplier": ["exact"],
        # }
