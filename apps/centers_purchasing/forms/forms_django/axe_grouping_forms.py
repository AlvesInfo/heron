"""Forms des dictionnaires Axe Pro/Regroupement de facturation."""

from django import forms

from apps.centers_purchasing.models import AxeProGroupingGoods
from apps.parameters.forms.forms_django.const_forms import SELECT_FLUIDE_DICT


class AxeProGroupingGoodsForm(forms.ModelForm):
    """Formulaires de la liste des dictionnaires Axe Pro/Regroupement de facturation."""

    use_required_attribute = False

    class Meta:
        """class Meta du form django."""

        model = AxeProGroupingGoods
        fields = [
            "axe_pro",
            "grouping_goods",
        ]
        widgets = {
            "axe_pro": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "grouping_goods": forms.Select(attrs=SELECT_FLUIDE_DICT),
        }


class AxeProGroupingGoodsDeleteForm(forms.ModelForm):
    """Formulaires de la liste des dictionnaires Axe Pro/Regroupement de facturation."""

    # Le champ id (AutoField) n\'est pas généré par le ModelForm : déclaré pour valider l\'existence
    id = forms.ModelChoiceField(queryset=AxeProGroupingGoods.objects.all())

    class Meta:
        """class Meta du form django."""

        model = AxeProGroupingGoods
        fields = [
            "id",
        ]
