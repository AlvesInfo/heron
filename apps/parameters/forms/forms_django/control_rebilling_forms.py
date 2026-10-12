"""Forms des Parameters pour les Contrôles de Refacturation."""

from django import forms

from apps.parameters.models import ControlRebilling


class ControlRebillingForm(forms.ModelForm):
    """Form pour les Contrôles de Refacturation."""

    use_required_attribute = False

    class Meta:
        """class Meta."""

        model = ControlRebilling
        fields = ("name", "comment")


class DeleteControlRebillingForm(forms.ModelForm):
    """Form pour la suppression des Contrôles de Refacturation."""

    # Le champ id (AutoField) n'est pas généré par le ModelForm : déclaré pour valider l'existence
    id = forms.ModelChoiceField(queryset=ControlRebilling.objects.all())

    class Meta:
        """class Meta."""

        model = ControlRebilling
        fields = ("id",)
