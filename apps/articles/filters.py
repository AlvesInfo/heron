# pylint: disable=E0401,R0903
"""
Filtres pour des recherches dans les views
"""
from django import forms
from django.db.models import Exists, OuterRef, Count
import django_filters
from django.db import models

from apps.accountancy.models import SectionSage, VatSage
from apps.articles.models import Article, ArticleAccount
from apps.book.models import Society
from apps.centers_purchasing.models import ChildCenterPurchase
from apps.parameters.models import Category, SubCategory
from apps.parameters.forms.forms_django.const_forms import SELECT_FLUIDE_DICT


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

    child_center = django_filters.ModelChoiceFilter(
        field_name="child_center",
        queryset=ChildCenterPurchase.objects.all(),
        to_field_name="code",
        widget=forms.Select(attrs=SELECT_FLUIDE_DICT),
    )
    third_party_num = django_filters.ModelChoiceFilter(
        field_name="article__third_party_num",
        queryset=Society.objects.filter(
            Exists(
                Article.objects.filter(
                    Exists(ArticleAccount.objects.filter(article=OuterRef("uuid_identification"))),
                    third_party_num=OuterRef("third_party_num"),
                )
            )
        ),
        to_field_name="third_party_num",
        widget=forms.Select(attrs=SELECT_FLUIDE_DICT),
    )
    reference = django_filters.CharFilter(
        field_name="article__reference", lookup_expr="icontains"
    )
    libelle = django_filters.CharFilter(
        field_name="libelle_article", lookup_expr="icontains"
    )
    axe_pro = django_filters.ModelChoiceFilter(
        field_name="article__axe_pro",
        queryset=SectionSage.objects.filter(axe="PRO"),
        to_field_name="uuid_identification",
        widget=forms.Select(attrs=SELECT_FLUIDE_DICT),
    )
    big_category = django_filters.ModelChoiceFilter(
        field_name="article__big_category",
        queryset=Category.objects.all(),
        to_field_name="uuid_identification",
        widget=forms.Select(attrs=SELECT_FLUIDE_DICT),
    )
    sub_category = django_filters.ModelChoiceFilter(
        field_name="article__sub_category",
        queryset=SubCategory.objects.all(),
        to_field_name="uuid_identification",
        widget=forms.Select(attrs=SELECT_FLUIDE_DICT),
    )
    vat = django_filters.ModelChoiceFilter(
        field_name="vat",
        queryset=VatSage.objects.all(),
        to_field_name="vat",
        widget=forms.Select(attrs=SELECT_FLUIDE_DICT),
    )
    purchase_account = django_filters.CharFilter(
        field_name="purchase_account", lookup_expr="icontains"
    )
    sale_account = django_filters.CharFilter(
        field_name="sale_account", lookup_expr="icontains"
    )

    class Meta:
        """class Meta django"""

        model = ArticleAccount
        fields = [
            "child_center",
            "third_party_num",
            "reference",
            "libelle",
            "axe_pro",
            "big_category",
            "sub_category",
            "vat",
            "purchase_account",
            "sale_account",
        ]
