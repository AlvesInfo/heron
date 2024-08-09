# pylint: disable=E0401,R0903
"""
Forms des rfa SectionProExclusion
"""
from django import forms

from apps.parameters.forms.forms_django.const_forms import SELECT_FLUIDE_DICT
from apps.rfa.models import SectionProExclusion


class SectionProExclusionForm(forms.ModelForm):
    """Form pour les exclusions des axes PRO"""

    class Meta:
        """class Meta"""

        model = SectionProExclusion
        fields = (
            "axe_pro",
        )
        widgets = {
            "axe_pro": forms.Select(attrs=SELECT_FLUIDE_DICT),
        }


class DeleteSectionProExclusionForm(forms.ModelForm):
    """Form pour la suppression des exclusions des axes PRO"""

    class Meta:
        """class Meta"""

        model = SectionProExclusion
        fields = ("id", )
