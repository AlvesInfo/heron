# pylint: disable=E0401,R0903
"""
Forms des Parameters pour les Contrôles de Refacturation
"""
from django import forms

from apps.parameters.models import ControlRebilling


class ControlRebillingForm(forms.ModelForm):
    """Form pour les Contrôles de Refacturation"""

    class Meta:
        """class Meta"""

        model = ControlRebilling
        fields = (
            "name",
            "comment"
        )


class DeleteControlRebillingForm(forms.ModelForm):
    """Form pour la suppression des Contrôles de Refacturation"""

    class Meta:
        """class Meta"""

        model = ControlRebilling
        fields = ("id", )
