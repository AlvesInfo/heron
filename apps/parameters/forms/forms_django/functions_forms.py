# pylint: disable=E0401,R0903
"""
Forms des Parameters
"""
from django import forms

from apps.parameters.forms.forms_django.const_forms import SELECT_FLUIDE_DICT
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


class DeleteInvoiceFunctionsForm(forms.ModelForm):
    """Form pour la suppression des InvoiceFunctions"""

    class Meta:
        """class Meta"""

        model = InvoiceFunctions
        fields = ("id", )