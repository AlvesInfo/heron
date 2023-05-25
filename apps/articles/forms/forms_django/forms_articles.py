# pylint: disable=E0401,R0903
"""
Forms des Parameters
"""
from django import forms

from apps.parameters.forms.forms_django.const_forms import SELECT_FLUIDE_DICT
from apps.articles.models import (
    Article,
)


class ArticleForm(forms.ModelForm):
    """Form de gestion des articles"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sub_category"].required = False

    class Meta:
        """class Meta django"""

        model = Article
        fields = [
            "third_party_num",
            "big_category",
            "sub_category",
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
            "customs_item_weight",
            "customs_unit_weight",
        ]

        widgets = {
            "third_party_num": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "big_category": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "sub_category": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "sub_familly": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "budget_code": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "made_in": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "unit_weight": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "axe_bu": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "axe_prj": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "axe_pro": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "axe_pys": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "axe_rfa": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "customs_unit_weight": forms.Select(attrs=SELECT_FLUIDE_DICT),
        }
