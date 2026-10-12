"""Forms des axes Rfa à positionner."""

from typing import cast

from django import forms

from apps.accountancy.models import SectionSage
from apps.parameters.forms.forms_django.const_forms import SELECT_FLUIDE_DICT
from apps.rfa.bin.rfa_controls import get_axe_rfa_period


class AxeRfaForm(forms.Form):
    """Choix de la section de l'axe RFA (période) pour la génération des RFA."""

    section = forms.ChoiceField(
        choices=(),
        widget=forms.Select(attrs=SELECT_FLUIDE_DICT),
        label="Axe RFA",
        required=True,
    )

    def __init__(self, *args, **kwargs):
        """Alimente les sections de l'axe RFA."""
        super().__init__(*args, **kwargs)
        cast(forms.ChoiceField, self.fields["section"]).choices = [
            (row.section, row.section)
            for row in SectionSage.objects.filter(axe__axe="RFA").order_by("section")
        ]
        self.fields["section"].initial = get_axe_rfa_period()
