"""
Forms des Familles Client
"""
from django import forms
from apps.centers_clients.models import ClientFamilly


class ClientFamillyForm(forms.ModelForm):
    """Formulaires des Familles Client"""

    class Meta:
        model = ClientFamilly
        fields = [
            "name",
            "comment",
        ]


class ClientFamillyDeleteForm(forms.ModelForm):
    """Formulaires des Familles Client à supprimer"""

    class Meta:
        model = ClientFamilly
        fields = [
            "id",
        ]