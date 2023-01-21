# pylint: disable=E0401,R0903
"""
Forms des dictionnaires Axe Pro/Regroupement de facturation
"""
from django import forms

from apps.parameters.forms.forms_django.const_forms import SELECT_FLUIDE_DICT
from apps.centers_purchasing.models import AxeProGroupingGoods


class AxeProGroupingGoodsForm(forms.ModelForm):
    """Formulaires de la liste des dictionnaires Axe Pro/Regroupement de facturation"""

    class Meta:
        """class Meta du form django"""

        model = AxeProGroupingGoods
        fields = [
            "axe_pro",
            "grouping_goods",
        ]
        widgets = {
            "axe_pro": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "grouping_goods": forms.Select(attrs=SELECT_FLUIDE_DICT),
        }


class AxeProGroupingGoodsDeleteForm(forms.ModelForm):
    """Formulaires de la liste des dictionnaires Axe Pro/Regroupement de facturation"""

    class Meta:
        """class Meta du form django"""

        model = AxeProGroupingGoods
        fields = [
            "id",
        ]
