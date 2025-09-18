# pylint: disable=E0401,R0903
"""
Forms des Parameters
"""
from django import forms

from apps.parameters.forms import NumberInput
from apps.parameters.forms.forms_django.const_forms import SELECT_FLUIDE_DICT
from apps.articles.models import Article
from apps.centers_clients.models import MaisonSubcription


class MaisonSubcriptionForm(forms.ModelForm):
    """Form pour les MaisonSubcription"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["article"].queryset = Article.objects.filter(
            big_category__slug_name__in={
                "redevances",
                "redevances-de-publicite",
                "prestation",
                "abonnements",
            }
        )

    class Meta:
        """class Meta"""

        model = MaisonSubcription
        fields = (
            "maison",
            "article",
            "qty",
            "unit_weight",
            "net_unit_price",
            "function",
            "for_signboard",
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
        }


class DeleteMaisonSubcriptionForm(forms.ModelForm):
    """Form pour la suppression des MaisonSubcription"""

    class Meta:
        """class Meta"""

        model = MaisonSubcription
        fields = ("id",)
