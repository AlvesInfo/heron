"""
Forms des rfa SectionProExclusion
"""
from django import forms

from apps.parameters.forms.forms_django.const_forms import SELECT_FLUIDE_DICT
from apps.rfa.models import SectionProExclusion


class SectionProExclusionForm(forms.ModelForm):
    """Form pour les exclusions des axes PRO"""

    use_required_attribute = False

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

    # Le champ id (AutoField) n'est pas généré par le ModelForm : déclaré pour valider l'existence
    id = forms.ModelChoiceField(queryset=SectionProExclusion.objects.all())

    class Meta:
        """class Meta"""

        model = SectionProExclusion
        fields = ("id", )
