"""
Forms des rfa ClientExclusion
"""
from django import forms

from apps.parameters.forms.forms_django.const_forms import SELECT_FLUIDE_DICT
from apps.rfa.models import ClientExclusion


class ClientExclusionForm(forms.ModelForm):
    """Form pour les exclusions des clients"""

    use_required_attribute = False

    class Meta:
        """class Meta"""

        model = ClientExclusion
        fields = (
            "cct",
        )
        widgets = {
            "cct": forms.Select(attrs=SELECT_FLUIDE_DICT),
        }


class DeleteClientExclusionForm(forms.ModelForm):
    """Form pour la suppression des exclusions des clients"""

    # Le champ id (AutoField) n'est pas généré par le ModelForm : déclaré pour valider l'existence
    id = forms.ModelChoiceField(queryset=ClientExclusion.objects.all())

    class Meta:
        """class Meta"""

        model = ClientExclusion
        fields = ("id", )
