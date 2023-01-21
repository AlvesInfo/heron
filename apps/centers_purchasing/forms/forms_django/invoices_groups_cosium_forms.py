# pylint: disable=E0401,R0903
"""
Forms des dictionnaires famille_acuitis - code_rayon_acuitis - axes_pro
"""
from django import forms

from apps.parameters.forms.forms_django.const_forms import SELECT_FLUIDE_DICT
from apps.centers_purchasing.models import AxeProFamilleCosium


class AxeProFamilleCosiumForm(forms.ModelForm):
    """Formulaires de la liste des dictionnaires famille_acuitis - code_rayon_acuitis - axes_pro"""

    class Meta:
        """class Meta du form django"""

        model = AxeProFamilleCosium
        fields = [
            "code_famille_cosium",
            "axe_pro",
        ]
        widgets = {
            "axe_pro": forms.Select(attrs=SELECT_FLUIDE_DICT),
        }


class AxeProFamilleCosiumDeleteForm(forms.ModelForm):
    """Formulaires de la liste des dictionnaires famille_acuitis - code_rayon_acuitis - axes_pro"""

    class Meta:
        """class Meta du form django"""

        model = AxeProFamilleCosium
        fields = [
            "id",
        ]
