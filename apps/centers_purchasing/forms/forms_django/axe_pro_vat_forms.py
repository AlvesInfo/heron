# pylint: disable=E0401,R0903
"""
Forms des dictionnaires Axe Pro/Regroupement de facturation
"""
from django import forms

from apps.parameters.forms.forms_django.const_forms import SELECT_FLUIDE_DICT
from apps.centers_purchasing.models import ApplicableProVat


class ApplicableProVatForm(forms.ModelForm):
    """Formulaires de la liste des dictionnaires Axe Pro/Regroupement de facturation"""

    class Meta:
        """class Meta du form django"""

        model = ApplicableProVat
        fields = [
            "child_center",
            "axe_pro",
            "vat",
        ]
        widgets = {
            "child_center": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "axe_pro": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "vat": forms.Select(attrs=SELECT_FLUIDE_DICT),
        }


class ApplicableProVatDeleteForm(forms.ModelForm):
    """Formulaires de la liste des dictionnaires Axe Pro/Regroupement de facturation"""

    class Meta:
        """class Meta du form django"""

        model = ApplicableProVat
        fields = [
            "id",
        ]
