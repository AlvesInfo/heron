"""
Forms des Parameters
"""
from django import forms

from apps.parameters.models import InvoiceFunctions


class InvoiceFunctionsForm(forms.ModelForm):
    """Form pour les InvoiceFunctions"""

    use_required_attribute = False

    class Meta:
        """class Meta"""

        model = InvoiceFunctions
        fields = (
            "function_name",
            "function",
            "absolute_path_windows",
            "absolute_path_linux",
            "description",
            "redirect",
        )
