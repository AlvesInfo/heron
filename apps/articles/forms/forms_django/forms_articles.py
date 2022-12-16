# pylint: disable=E0401,R0903
"""
Forms des Parameters
"""
from django import forms

from apps.articles.models import (
    Article,
)


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = [
            "active",
            "delete",
            "third_party_num",
            "reference",
            "ean_code",
            "libelle",
            "libelle_heron",
            "brand",
            "manufacturer",
            "big_category",
            "sub_familly",
            "budget_code",
            "famille_supplier",
            "axe_pro_supplier",
            "axe_bu",
            "axe_prj",
            "axe_pro",
            "axe_pys",
            "axe_rfa",
            "made_in",
            "item_weight",
            "unit_weight",
            "packaging_qty",
            "customs_code",
            "catalog_price",
            "comment",
            "new_article",
        ]
