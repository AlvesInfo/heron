# pylint: disable=E0401,R0903
"""
Filtres pour des recherches dans les views
"""
from django import forms
from django.db.models import Exists, OuterRef, Count
import django_filters
from django.db import models

from apps.articles.models import Article, ArticleAccount
from apps.book.models import Society


class ArticleFilter(django_filters.FilterSet):
    """Filtre des articles"""

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
