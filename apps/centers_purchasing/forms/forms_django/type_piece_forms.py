# pylint: disable=E0401,R0903
"""
Forms des dictionnaires Centrale FIlle / Type de pièces
"""
from django import forms

from apps.parameters.forms.forms_django.const_forms import SELECT_FLUIDE_DICT
from apps.centers_purchasing.models import TypePiece


class TypePieceForm(forms.ModelForm):
    """Formulaires de la liste des dictionnaires Centrale FIlle / Type de pièces"""

    class Meta:
        """class Meta du form django"""

        model = TypePiece
        fields = [
            "child_center",
            "invoice_type",
            "purchase_type_piece",
            "sale_type_piece",
        ]
        widgets = {
            "child_center": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "invoice_type": forms.Select(attrs=SELECT_FLUIDE_DICT),
        }


class TypePieceDeleteForm(forms.ModelForm):
    """Formulaires de la liste des dictionnaires Centrale FIlle / Type de pièces"""

    class Meta:
        """class Meta du form django"""

        model = TypePiece
        fields = [
            "id",
        ]
