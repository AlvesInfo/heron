"""Forms des rfa SectionRfa."""

from django import forms

from apps.parameters.forms.forms_django.const_forms import SELECT_FLUIDE_DICT
from apps.rfa.models import SectionRfa


class SectionRfaForm(forms.ModelForm):
    """Form pour les axes RFA."""

    use_required_attribute = False

    class Meta:
        """class Meta."""

        model = SectionRfa
        fields = ("axe_rfa",)
        widgets = {
            "axe_rfa": forms.Select(attrs=SELECT_FLUIDE_DICT),
        }


class DeleteSectionRfaForm(forms.ModelForm):
    """Form pour la suppression des axes RFA."""

    # Le champ id (AutoField) n'est pas généré par le ModelForm : déclaré pour valider l'existence
    id = forms.ModelChoiceField(queryset=SectionRfa.objects.all())

    class Meta:
        """class Meta."""

        model = SectionRfa
        fields = ("id",)
