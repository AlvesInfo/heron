"""FR : Module des formulaires pour l'objet Nature/Genre.

EN : Forms module for the Nature Gender object.

Commentaire:

created at: 2023-03-13
created by: Paulo ALVES

modified at: 2023-03-13
modified by: Paulo ALVES
"""

from django import forms

from apps.parameters.models import Nature


class NatureForm(forms.ModelForm):
    """Form pour les Natures/Genres."""

    use_required_attribute = False

    class Meta:
        """class Meta."""

        model = Nature
        fields = (
            "id",
            "name",
            "to_display",
            "for_contact",
            "for_personnel",
            "for_formation",
        )
