# pylint: disable=E0401,R0903
"""
Forms des dictionnaires des Comptes debit crédit pour la facturation
"""
from django import forms

from apps.parameters.forms.forms_django.const_forms import SELECT_FLUIDE_DICT
from apps.centers_purchasing.models import AccountsAxeProCategory


class AccountsAxeProCategoryForm(forms.ModelForm):
    """Formulaires de la liste des dictionnaires des Comptes debit crédit pour la facturation"""

    class Meta:
        """class Meta du form django"""

        model = AccountsAxeProCategory
        fields = [
            "child_center",
            "big_category",
            "axe_pro",
            "vat",
            "purchase_account",
            "sale_account",
        ]
        widgets = {
            "child_center": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "big_category": forms.Select(attrs=SELECT_FLUIDE_DICT),
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
