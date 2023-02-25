# pylint: disable=E0401,R0903
"""
Forms des Parameters
"""
from django import forms

from apps.parameters.forms.forms_django.const_forms import SELECT_FLUIDE_DICT
from apps.book.models import StatFamillyAxes, SupplierFamilyAxes


class StatFamillyAxesForm(forms.ModelForm):
    """Form pour les Statistiques"""

    class Meta:
        """class Meta"""

        model = StatFamillyAxes
        fields = ("name", "description", "regex_bool")


class SupplierFamilyAxesForm(forms.ModelForm):
    """Form pour les définitions des Statistiques Familles/Axes'"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sub_category"].required = False

    class Meta:
        """class Meta"""

        model = SupplierFamilyAxes
        fields = (
            "id",
            "stat_name",
            "invoice_column",
            "regex_match",
            "expected_result",
            "axe_pro",
            "description",
            "norme",
            "comment",
            "big_category",
            "sub_category",
            "item_weight",
            "unit_weight",
            "customs_code",
        )
        widgets = {
            "axe_pro": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "big_category": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "sub_category": forms.Select(attrs=SELECT_FLUIDE_DICT),
        }


class DeleteSupplierFamilyAxesForm(forms.ModelForm):
    """Form pour la suppression des définitions des Statistiques Familles/Axes"""

    class Meta:
        """class Meta"""

        model = SupplierFamilyAxes
        fields = ("id",)
