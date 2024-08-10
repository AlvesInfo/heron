# pylint: disable=E0401,R0903
"""
Forms des axes Rfa à positionner
"""
from django import forms

from apps.parameters.forms.forms_django.const_forms import SELECT_FLUIDE_DICT
from apps.accountancy.models import SectionSage
from apps.rfa.bin.rfa_controls import get_axe_rfa_period


class AxeRfaForm(forms.ModelForm):
    """Ajout ou transformation des champs de formulaires"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        initial = get_axe_rfa_period()
        self.section_choices = (
            (row.section, row.section)
            for row in SectionSage.objects.filter(axe="RFA").order_by("section")
        )
        section = forms.ChoiceField(
            choices=self.section_choices,
            widget=forms.Select(attrs=SELECT_FLUIDE_DICT),
            label="Axe RFA",
            required=True,
            initial=(initial, initial),
        )
        self.fields["section"] = section

    class Meta:
        """class Meta"""

        model = SectionSage
        fields = [
            "section",
        ]
        widgets = {
            "section": forms.Select(attrs=SELECT_FLUIDE_DICT),
        }
