# pylint: disable=E0401, R0903
"""
Forms des paramètres pour les Periodes
"""
from typing import Dict

import pendulum
from django import forms

from apps.parameters.forms.forms_django.const_forms import SELECT_FLUIDE_DICT


def get_month_choices() -> Dict:
    """Retourne les choix possibles pour la période mois et la valeur initiale.
    Les valeurs retournées sont M - 12 à M + 12
    :return:
    """
    period_dict = {"initial": None, "periods": []}

    for i in range(-12, 13):
        month = pendulum.now().add(months=i)
        value = (
            f"{month.start_of('month').date().isoformat()}"
            "_"
            f"{month.end_of('month').date().isoformat()}"
        )
        text_value = f"{month.format('MMMM YYYY', locale='fr')}".capitalize()
        period_dict["periods"].append((value, text_value))

        if i == -1:
            period_dict["initial"] = (value, text_value)

    return period_dict


def get_year_choices() -> Dict:
    """Retourne les choix possibles pour la période année et la valeur initiale.
    Les valeurs retournées sont Y - 10 à Y + 10
    :return:
    """
    period_dict = {"initial": None, "periods": []}

    for i in range(-10, 11):
        dte_year = pendulum.now().add(years=i)
        value = str(dte_year.year)
        text_value = f"Année {str(dte_year.year)}"
        period_dict["periods"].append((value, text_value))

        if i == 0:
            period_dict["initial"] = (value, text_value)

    return period_dict


class MonthForm(forms.Form):
    """Form pour les Périodes de type Mois"""

    periode = forms.ChoiceField(
        required=True,
        widget=forms.Select(attrs=SELECT_FLUIDE_DICT),
        choices=tuple(),
        label="Période",
        help_text="Vous devez sélectionner au moins une Période",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        choices_dict = get_month_choices()

        initial = choices_dict.get("initial")
        choices = choices_dict.get("periods")

        self.fields["periode"].choices = choices
        self.fields["periode"].initial = initial


class YearForm(forms.ModelForm):
    """Form pour les Périodes de type Années"""

    periode = forms.ChoiceField(
        required=True,
        widget=forms.Select(attrs=SELECT_FLUIDE_DICT),
        choices=tuple(),
        label="Période",
        help_text="Vous devez sélectionner au moins une Année",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        choices_dict = get_month_choices()

        initial = choices_dict.get("initial")
        choices = choices_dict.get("periods")

        self.fields["periode"].choices = choices
        self.fields["periode"].initial = initial
