# pylint: disable=E0401,R0903
"""
Forms des dictionnaires des Comptes debit crédit pour la facturation
"""
from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Value, CharField
from django.db.models.functions import Coalesce, Cast

from apps.parameters.forms.forms_django.const_forms import SELECT_FLUIDE_DICT
from apps.centers_purchasing.models import AccountsAxeProCategory


class AccountsAxeProCategoryForm(forms.ModelForm):
    """Formulaires de la liste des dictionnaires des Comptes debit crédit pour la facturation"""

    def __init__(self, *args, **kwargs):
        """Ajout ou transformation des champs de formulaires"""
        super().__init__(*args, **kwargs)
        self.fields["sub_category"].required = False

    def clean(self):
        """Netoyage de la clefs multiple à cause de sub_category qui peut être null"""
        cleaned_data = super().clean()
        child_center = cleaned_data.get("child_center", "")
        big_category = cleaned_data.get("big_category", "")
        sub_category = cleaned_data.get("sub_category", "")
        axe_pro = cleaned_data.get("axe_pro", "")
        vat = cleaned_data.get("vat", "")

        accounts = (
            AccountsAxeProCategory.objects.annotate(
                sub_categoryc=Coalesce(Cast("sub_category", output_field=CharField()), Value(""))
            )
            .filter(
                child_center=child_center,
                big_category=big_category,
                sub_categoryc=sub_category or "",
                axe_pro=axe_pro,
                vat=vat,
            )
            .values("pk")
            .exists()
        )

        if accounts:
            raise ValidationError("Un élément identique existe déjà!")

    class Meta:
        """class Meta du form django"""

        model = AccountsAxeProCategory
        fields = [
            "child_center",
            "big_category",
            "sub_category",
            "axe_pro",
            "vat",
            "purchase_account",
            "sale_account",
        ]
        widgets = {
            "child_center": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "big_category": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "sub_category": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "axe_pro": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "vat": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "purchase_account": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "sale_account": forms.Select(attrs=SELECT_FLUIDE_DICT),
        }


class AccountsAxeProCategoryDeleteForm(forms.ModelForm):
    """Formulaires de la liste des dictionnaires des Comptes debit crédit pour la facturation"""

    class Meta:
        """class Meta du form django"""

        model = AccountsAxeProCategory
        fields = [
            "id",
        ]
