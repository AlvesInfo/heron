# pylint: disable=E0401,R0903, E1101
"""
FR : Module des formulaires pour l'objet Nature/Genre
EN : Forms module for the Nature Gender object

Commentaire:

created at: 2023-03-13
created by: Paulo ALVES

modified at: 2023-03-13
modified by: Paulo ALVES
"""
from django import forms

from apps.parameters.forms.forms_django.const_forms import SELECT_FLUIDE_DICT
from apps.parameters.models import Nature


class NatureForm(forms.ModelForm):
    """Form pour les Natures/Genres"""

    class Meta:
        """class Meta"""

        model = Nature
        fields = (
            "id",
            "name",
            "to_display",
            "for_contact",
            "for_personnel",
            "for_formation",
        )
