# pylint: disable=E0401,R0903
"""
Forms des rfa SignboardExclusion
"""
from django import forms

from apps.parameters.forms.forms_django.const_forms import SELECT_FLUIDE_DICT
from apps.rfa.models import SignboardExclusion


class SignboardExclusionForm(forms.ModelForm):
    """Form pour les exclusions d'Enseignes"""

    class Meta:
        """class Meta"""

        model = SignboardExclusion
        fields = (
            "signboard",
        )
        widgets = {
            "big_category": forms.Select(attrs=SELECT_FLUIDE_DICT),
        }


class DeleteSignboardExclusionForm(forms.ModelForm):
    """Form pour la suppression des exclusions d'Enseignes"""

    class Meta:
        """class Meta"""

        model = SignboardExclusion
        fields = ("id", )
