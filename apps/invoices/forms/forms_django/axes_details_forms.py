"""Forms des dictionnaires Axe Pro/Regroupement de facturation."""

from django import forms

from apps.invoices.models import AxesDetails, EnteteDetails
from apps.parameters.forms.forms_django.const_forms import SELECT_FLUIDE_DICT


class EnteteDetailsForm(forms.ModelForm):
    """Formulaires de la liste des dictionnaires Entêtes Détails de facturation."""

    use_required_attribute = False

    class Meta:
        """class Meta du form django."""

        model = EnteteDetails
        fields = [
            "ranking",
            "column_name",
        ]


class EnteteDetailsDeleteForm(forms.ModelForm):
    """Formulaire de suppression d'une entête de détails (l'id doit exister)."""

    id = forms.ModelChoiceField(queryset=EnteteDetails.objects.all())

    class Meta:
        """class Meta du form django."""

        model = EnteteDetails
        fields = [
            "id",
        ]


class AxesDetailsForm(forms.ModelForm):
    """Formulaires de la liste des dictionnaires Axe Pro/Détails de facturation."""

    use_required_attribute = False

    class Meta:
        """class Meta du form django."""

        model = AxesDetails
        fields = [
            "axe_pro",
            "column_name",
        ]
        widgets = {
            "axe_pro": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "column_name": forms.Select(attrs=SELECT_FLUIDE_DICT),
        }


class AxesDetailsDeleteForm(forms.ModelForm):
    """Formulaire de suppression d'un couple axe pro / entête (l'id doit exister)."""

    id = forms.ModelChoiceField(queryset=AxesDetails.objects.all())

    class Meta:
        """class Meta du form django."""

        model = AxesDetails
        fields = [
            "id",
        ]
