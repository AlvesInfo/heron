# pylint: disable=E0401,R0903
"""
Forms des Parameters
"""
from django import forms

from apps.parameters.models import InvoiceFunctions


class InvoiceFunctionsForm(forms.ModelForm):
    """Form pour les InvoiceFunctions"""

    class Meta:
        """class Meta"""

        model = InvoiceFunctions
        fields = (
            "function_name",
            "function",
            "absolute_path_windows",
            "absolute_path_linux",
            "description",
        )