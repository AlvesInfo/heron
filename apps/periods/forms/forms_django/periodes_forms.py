"""Forms des paramètres pour les Periodes."""

from typing import Any, cast

import pendulum
from django import forms
from django.db.models import Min

from apps.invoices.models import SaleInvoice
from apps.parameters.forms.forms_django.const_forms import SELECT_FLUIDE_DICT


def get_month_choices() -> dict:
    """Retourne les choix possibles pour la période mois et la valeur initiale.

    Les valeurs retournées sont M - 12 à M + 12
    :return:
    """
    period_dict: dict[str, Any] = {"initial": None, "periods": []}

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


def get_year_choices() -> dict:
    """Retourne les choix possibles pour la période année et la valeur initiale.

    Les valeurs retournées sont Y - 10 à Y + 10, l'initiale est l'année en cours
    :return: {"initial": (valeur, libellé), "periods": [(valeur, libellé), ...]}.
    """
    period_dict: dict[str, Any] = {"initial": None, "periods": []}
    year = pendulum.now().year

    for i in range(year - 10, year + 11):
        choice = (str(i), f"Année {i}")
        period_dict["periods"].append(choice)

        if i == year:
            period_dict["initial"] = choice

    return period_dict


def get_year_passed_choices() -> dict:
    """Retourne les choix possibles pour les années facturées et la valeur initiale.

    Les valeurs retournées vont de la première année de facture de vente à l'année en cours
    (seule l'année en cours s'il n'y a aucune facture), l'initiale est l'année en cours
    :return: {"initial": (valeur, libellé), "periods": [(valeur, libellé), ...]}.
    """
    period_dict: dict[str, Any] = {"initial": None, "periods": []}
    year = pendulum.now().year
    first_year = SaleInvoice.objects.aggregate(year=Min("invoice_year")).get("year") or year

    for i in range(min(first_year, year), year + 1):
        choice = (str(i), f"Année {i}")
        period_dict["periods"].append(choice)

        if i == year:
            period_dict["initial"] = choice

    return period_dict


class MonthForm(forms.Form):
    """Form pour les Périodes de type Mois."""

    periode = forms.ChoiceField(
        required=True,
        widget=forms.Select(attrs=SELECT_FLUIDE_DICT),
        choices=(),
        label="Période",
        help_text="Vous devez sélectionner au moins une Période",
    )

    def __init__(self, *args, **kwargs):
        """Alimente les choix de mois et la valeur initiale."""
        super().__init__(*args, **kwargs)

        choices_dict = get_month_choices()

        initial = choices_dict.get("initial")
        choices = choices_dict["periods"]

        cast(forms.ChoiceField, self.fields["periode"]).choices = choices
        self.fields["periode"].initial = initial


class YearForm(forms.Form):
    """Form pour les Périodes de type Année (valeur : l'année sur 4 chiffres)."""

    periode = forms.ChoiceField(
        required=True,
        widget=forms.Select(attrs=SELECT_FLUIDE_DICT),
        choices=(),
        label="Année",
        help_text="Vous devez sélectionner une Année",
    )

    def __init__(self, *args, **kwargs):
        """Alimente les choix d'années et la valeur initiale."""
        super().__init__(*args, **kwargs)
        choices_dict = get_year_choices()
        cast(forms.ChoiceField, self.fields["periode"]).choices = choices_dict["periods"]
        self.fields["periode"].initial = choices_dict.get("initial")


class YearPassedForm(forms.Form):
    """Form des Années facturées (de la première facture de vente à l'année en cours)."""

    periode = forms.ChoiceField(
        required=True,
        widget=forms.Select(attrs=SELECT_FLUIDE_DICT),
        choices=(),
        label="Année",
        help_text="Vous devez sélectionner une Année",
    )

    def __init__(self, *args, **kwargs):
        """Alimente les choix d'années passées et la valeur initiale."""
        super().__init__(*args, **kwargs)
        choices_dict = get_year_passed_choices()
        cast(forms.ChoiceField, self.fields["periode"]).choices = choices_dict["periods"]
        self.fields["periode"].initial = choices_dict.get("initial")
