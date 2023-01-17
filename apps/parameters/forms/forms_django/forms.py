# pylint: disable=E0401,R0903, E1101
"""
FR : Module pour l'héritage des choices fields
EN : Module for choice fields inheritance

Commentaire:

created at: 2023-01-17
created by: Paulo ALVES

modified at: 2023-01-17
modified by: Paulo ALVES
"""
from django import forms

from apps.parameters.models import Category


def get_category_select():
    """Sélect des choices fields"""
    big_category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        # widget=forms.Select(attrs={"class": "ui fluid search dropdown"})
    )

    return big_category
