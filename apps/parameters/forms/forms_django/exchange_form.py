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

    use_required_attribute = False
    def __init__(self, *args, **kwargs):
        """initialisation de la classe"""
        super().__init__(*args, **kwargs)
        # Fixés par la vue : affichés mais jamais repris du POST (sinon écrasés à None)
        for name in ("curency_base", "rate_month"):
            self.fields[name].required = False
            self.fields[name].disabled = True

    class Meta:
        """class meta django"""

        model = ExchangeRate
        fields = ["curency_base", "currency_change", "rate_month", "rate"]
        widgets = {"currency_change": forms.Select(attrs=SELECT_FLUIDE_DICT)}
