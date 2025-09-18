# pylint: disable=E0401,R0903
"""
Forms des dictionnaires Centrale FIlle / Type de pièces
"""
from django import forms

from apps.parameters.forms.forms_django.const_forms import SELECT_FLUIDE_DICT
from apps.centers_purchasing.models import TypeFacture


class TypeFactureForm(forms.ModelForm):
    """Formulaires de la liste des dictionnaires Centrale FIlle / Type de pièces"""

    class Meta:
        """class Meta du form django"""

        model = TypeFacture
        fields = [
            "child_center",
            "invoice_type",
            "purchase_type_facture",
            "sale_type_facture",
        ]
        widgets = {
            "child_center": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "invoice_type": forms.Select(attrs=SELECT_FLUIDE_DICT),
        }


class TypeFactureDeleteForm(forms.ModelForm):
    """Formulaires de la liste des dictionnaires Centrale FIlle / Type de pièces"""

    class Meta:
        """class Meta du form django"""

        model = TypeFacture
        fields = [
            "id",
        ]
