# pylint: disable=E0401,R0903
"""
Forms des Parameters
"""
from django import forms

from apps.parameters.forms.forms_django.const_forms import SELECT_FLUIDE_DICT
from apps.parameters.models import Category, SubCategory, DefaultAxeArticle


class CategoryForm(forms.ModelForm):
    """Form pour les Grandes catégories"""

    class Meta:
        """class Meta"""

        model = Category
        fields = (
            "ranking",
            "code",
            "name",
        )


class SubCategoryForm(forms.ModelForm):
    """Form pour les Rubriques presta'"""

    class Meta:
        """class Meta"""

        model = SubCategory
        fields = (
            "id",
            "big_category",
            "ranking",
            "code",
            "name",
        )
        widgets = {
            "big_category": forms.Select(attrs=SELECT_FLUIDE_DICT),
        }


class DeleteSubCategoryForm(forms.ModelForm):
    """Form pour la suppression des Rubriques Presta"""

    class Meta:
        """class Meta"""

        model = SubCategory
        fields = ("id", )


class DefaultAxeArticleForm(forms.ModelForm):
    """Form d'Update des axes par défaut des articles"""

    def __init__(self, *args, **kwargs):
        """Ajout ou transformation des champs de formulaires"""
        super().__init__(*args, **kwargs)

        self.fields["sub_category"].required = False

    class Meta:
        """class Meta"""

        model = DefaultAxeArticle
        fields = (
            "big_category",
            "sub_category",
            "axe_bu",
            "axe_prj",
            "axe_pys",
            "axe_rfa",
        )
        widgets = {
            "big_category": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "sub_category": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "axe_bu": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "axe_prj": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "axe_pys": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "axe_rfa": forms.Select(attrs=SELECT_FLUIDE_DICT),
        }
