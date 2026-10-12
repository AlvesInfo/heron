"""
Forms des rfa SignboardExclusion
"""
from django import forms

from apps.parameters.forms.forms_django.const_forms import SELECT_FLUIDE_DICT
from apps.rfa.models import SignboardExclusion


class SignboardExclusionForm(forms.ModelForm):
    """Form pour les exclusions d'Enseignes"""

    use_required_attribute = False

    class Meta:
        """class Meta"""

        model = SignboardExclusion
        fields = (
            "signboard",
        )
        widgets = {
            "signboard": forms.Select(attrs=SELECT_FLUIDE_DICT),
        }


class DeleteSignboardExclusionForm(forms.ModelForm):
    """Form pour la suppression des exclusions d'Enseignes"""

    # Le champ id (AutoField) n'est pas généré par le ModelForm : déclaré pour valider l'existence
    id = forms.ModelChoiceField(queryset=SignboardExclusion.objects.all())

    class Meta:
        """class Meta"""

        model = SignboardExclusion
        fields = ("id", )
