# pylint: disable=E0401,R0903, E1101
"""
FR : Module des formulaires pour l'objet numérotation (interne, externe, etc...)
EN : Forms module for the numbering object (internal, external, etc.)

Commentaire:

created at: 2023-03-23
created by: Paulo ALVES

modified at: 2023-03-23
modified by: Paulo ALVES
"""
from django import forms

from apps.parameters.forms.forms_django.const_forms import SELECT_FLUIDE_DICT
from apps.parameters.models import Counter


class CounterForm(forms.ModelForm):
    """Form pour les Compteurs"""

    def __init__(self, *args, **kwargs):
        """Ajout ou transformation des champs de formulaires"""
        super().__init__(*args, **kwargs)

        self.fields["lpad_num"].required = False
        self.fields["prefix"].required = False
        self.fields["suffix"].required = False
        self.fields["description"].required = False
        self.fields["separateur"].required = False

    class Meta:
        """class Meta"""

        model = Counter
        fields = (
            "id",
            "name",
            "prefix",
            "suffix",
            "fonction",
            "lpad_num",
            "description",
            "separateur",
        )
        widgets = {
            "fonction": forms.Select(attrs=SELECT_FLUIDE_DICT),
        }


class DeleteCounterForm(forms.ModelForm):
    """Form pour la suppression des InvoiceFunctions"""

    class Meta:
        """class Meta"""

        model = Counter
        fields = ("id",)
