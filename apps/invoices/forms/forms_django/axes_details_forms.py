# pylint: disable=E0401,R0903
"""
Forms des dictionnaires Axe Pro/Regroupement de facturation
"""
from django import forms

from apps.parameters.forms.forms_django.const_forms import SELECT_FLUIDE_DICT
from apps.invoices.models import EnteteDetails, AxesDetails


class EnteteDetailsForm(forms.ModelForm):
    """Formulaires de la liste des dictionnaires Entêtes Détails de facturation"""

    class Meta:
        """class Meta du form django"""

        model = EnteteDetails
        fields = [
            "ranking",
            "column_name",
        ]


class EnteteDetailsDeleteForm(forms.ModelForm):
    """Formulaires de la liste des dictionnaires Entêtes Détails de facturation"""

    class Meta:
        """class Meta du form django"""

        model = EnteteDetails
        fields = [
            "id",
        ]


class AxesDetailsForm(forms.ModelForm):
    """Formulaires de la liste des dictionnaires Axe Pro/Détails de facturation"""

    class Meta:
        """class Meta du form django"""

        model = AxesDetails
        fields = [
            "axe_pro",
            "column_name",
        ]
        widgets = {
            "axe_pro": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "column_name": forms.Select(attrs=SELECT_FLUIDE_DICT),
        }


class AxesDetailsDeleteForm(forms.ModelForm):
    """Formulaires de la liste des dictionnaires Axe Pro/Détails de facturation"""

    class Meta:
        """class Meta du form django"""

        model = AxesDetails
        fields = [
            "id",
        ]
