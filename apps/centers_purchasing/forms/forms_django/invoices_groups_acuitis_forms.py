# pylint: disable=E0401,R0903
"""
Forms des dictionnaires famille_acuitis - code_rayon_acuitis - axes_pro
"""
from django import forms

from apps.parameters.forms.forms_django.const_forms import SELECT_FLUIDE_DICT
from apps.centers_purchasing.models import AxeProFamilleAcuitis


class AxeProFamilleAcuitisForm(forms.ModelForm):
    """Formulaires de la liste des dictionnaires famille_acuitis - code_rayon_acuitis - axes_pro"""

    class Meta:
        """class Meta du form django"""

        model = AxeProFamilleAcuitis
        fields = [
            "code_famille_acuitis",
            "code_rayon_acuitis",
            "axe_pro",
        ]
        widgets = {
            "axe_pro": forms.Select(attrs=SELECT_FLUIDE_DICT),
        }


class AxeProFamilleAcuitisDeleteForm(forms.ModelForm):
    """Formulaires de la liste des dictionnaires famille_acuitis - code_rayon_acuitis - axes_pro"""

    class Meta:
        """class Meta du form django"""

        model = AxeProFamilleAcuitis
        fields = [
            "id",
        ]
