# pylint: disable=E0401,R0903
"""
Forms des Parameters
"""

from django import forms

from apps.parameters.forms.forms_django.const_forms import SELECT_FLUIDE_DICT
from apps.articles.models import (
    Article,
    ArticleAccount,
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


class ArticleSearchForm(forms.ModelForm):
    """Pour le Filtre de recherche des articles"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        reference_icontains = forms.CharField(
            label="Référence",
            required=False,
        )
        self.fields["reference__icontains"] = reference_icontains
        self.fields["reference__icontains"].required = False

        libelle_icontains = forms.CharField(
            label="Référence",
            required=False,
        )
        self.fields["libelle__icontains"] = libelle_icontains
        self.fields["libelle__icontains"].required = False

        libelle_heron_icontains = forms.CharField(
            label="Référence",
            required=False,
        )
        self.fields["libelle_heron__icontains"] = libelle_heron_icontains
        self.fields["libelle_heron__icontains"].required = False

        self.fields["third_party_num"].required = False
        self.fields["big_category"].required = False
        self.fields["sub_category"].required = False

    class Meta:
        """class Meta django"""

        model = Article
        fields = ("third_party_num", "big_category", "sub_category")
        widgets = {
            "third_party_num": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "big_category": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "sub_category": forms.Select(attrs=SELECT_FLUIDE_DICT),
        }


class ArticleAccountForm(forms.ModelForm):
    """Form pour les comptes par taux de tva des articles"""

    class Meta:
        """class Meta"""

        model = ArticleAccount
        fields = (
            "child_center",
            "article",
            "vat",
            "purchase_account",
            "sale_account",
        )
        widgets = {
            "child_center": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "article": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "vat": forms.Select(attrs=SELECT_FLUIDE_DICT),
        }


class DeleteArticleAccountForm(forms.ModelForm):
    """Form pour la suppression des comptes par taux de tva des articles"""

    class Meta:
        """class Meta"""

        model = ArticleAccount
        fields = ("id",)
