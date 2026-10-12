"""Forms des Familles Client."""

from django import forms

from apps.centers_clients.models import ClientFamilly


class ClientFamillyForm(forms.ModelForm):
    """Formulaires des Familles Client."""

    use_required_attribute = False

    class Meta:
        """Métadonnées Django : modèle et champs du formulaire."""

        model = ClientFamilly
        fields = [
            "name",
            "comment",
        ]


class ClientFamillyDeleteForm(forms.ModelForm):
    """Formulaires des Familles Client à supprimer."""

    id = forms.ModelChoiceField(queryset=ClientFamilly.objects.all())

    class Meta:
        """Métadonnées Django : modèle et champs du formulaire."""

        model = ClientFamilly
        fields = [
            "id",
        ]
