"""Forms des rfa SupplierRate."""

from django import forms

from apps.parameters.forms.forms_django.const_forms import SELECT_FLUIDE_DICT
from apps.rfa.models import SupplierRate


class SupplierRateForm(forms.ModelForm):
    """Form pour les taux de RFA."""

    use_required_attribute = False

    class Meta:
        """class Meta."""

        model = SupplierRate
        fields = ("supplier", "rfa_rate")
        widgets = {
            "supplier": forms.Select(attrs=SELECT_FLUIDE_DICT),
        }


class DeleteSupplierRateForm(forms.ModelForm):
    """Form pour la suppression des taux de RFA."""

    # Le champ id (AutoField) n'est pas généré par le ModelForm : déclaré pour valider l'existence
    id = forms.ModelChoiceField(queryset=SupplierRate.objects.all())

    class Meta:
        """class Meta."""

        model = SupplierRate
        fields = ("id",)
