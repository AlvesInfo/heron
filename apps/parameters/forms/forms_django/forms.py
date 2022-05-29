# pylint: disable=E0401,R0903
"""
Forms des Parameters
"""
from django import forms

from apps.parameters.models import (
    Category,
)


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = [
            "ranking",
            "name",
        ]