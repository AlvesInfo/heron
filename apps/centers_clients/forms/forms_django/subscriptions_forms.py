"""Forms des Parameters."""

from typing import cast

from django import forms

from apps.articles.models import Article
from apps.centers_clients.models import MaisonSubcription
from apps.core.bin.typing_helpers import required
from apps.parameters.forms import NumberInput
from apps.parameters.forms.forms_django.const_forms import SELECT_FLUIDE_DICT


class MaisonSubcriptionForm(forms.ModelForm):
    """Form pour les MaisonSubcription."""

    use_required_attribute = False

    def __init__(self, *args, **kwargs):
        """Restreint les maisons et les articles d'abonnement proposés."""
        super().__init__(*args, **kwargs)
        maison_field = cast(forms.ModelChoiceField, self.fields["maison"])
        maison_field.queryset = required(maison_field.queryset).select_related("cct")
        cast(
            forms.ModelChoiceField, self.fields["article"]
        ).queryset = Article.objects.select_related("third_party_num").filter(
            big_category__slug_name__in={
                "redevances",
                "redevances-de-publicite",
                "prestation",
                "abonnements",
                "divers",
            }
        )

    class Meta:
        """class Meta."""

        model = MaisonSubcription
        fields = (
            "maison",
            "article",
            "qty",
            "unit_weight",
            "net_unit_price",
            "function",
            "for_signboard",
            "vat",
        )
        widgets = {
            "maison": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "article": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "qty": NumberInput(attrs={"step": "1", "style": "text-align: right;"}),
            "unit_weight": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "net_unit_price": NumberInput(
                attrs={"step": "0.01", "min": 0, "style": "text-align: right;"}
            ),
            "function": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "for_signboard": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "vat": forms.Select(attrs=SELECT_FLUIDE_DICT),
        }


class DeleteMaisonSubcriptionForm(forms.ModelForm):
    """Form pour la suppression des MaisonSubcription."""

    id = forms.ModelChoiceField(queryset=MaisonSubcription.objects.all())

    class Meta:
        """class Meta."""

        model = MaisonSubcription
        fields = ("id",)
