# pylint: disable=E0401,R0903, E1101
"""
FR : Formulaire pour les taux de change
EN : Form for exchange rates

Commentaire:

created at: 2023-06-04
created by: Paulo ALVES

modified at: 2023-06-04
modified by: Paulo ALVES
"""
from django import forms

from apps.parameters.forms.forms_django.const_forms import SELECT_FLUIDE_DICT
from apps.parameters.models import ExchangeRate


class ExchangeRateForm(forms.ModelForm):
    """Formulaire des taux de change formset"""

    class Meta:
        """class meta django"""

        model = ExchangeRate
        fields = ["curency_base", "currency_change", "rate_month", "rate"]
        widgets = {"currency_change": forms.Select(attrs=SELECT_FLUIDE_DICT)}
