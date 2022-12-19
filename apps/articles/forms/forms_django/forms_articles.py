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
            # "id",
            "third_party_num",
            "big_category",
            "reference",
            "ean_code",
            "brand",
            "manufacturer",

            "libelle",
            "libelle_heron",
            "sub_familly",

            "budget_code",
            "famille_supplier",
            "axe_pro_supplier",
            "made_in",
            "item_weight",
            "unit_weight",
            "packaging_qty",

            "catalog_price",
            "axe_bu",
            "axe_prj",
            "axe_pro",
            "axe_pys",
            "axe_rfa",
            "customs_code",

            "comment",
            "new_article",
        ]
