# pylint: disable=E0401,R0903
"""
FR : Module des formulaires de validation des imports Sage X3
EN : Sage X3 import validation forms module

Commentaire:

created at: 2021-11-07
created by: Paulo ALVES

modified at: 2021-11-07
modified by: Paulo ALVES
"""
from django import forms

from apps.core.forms_validation.forms_base import SageNullBooleanField
from apps.accountancy.models import (
    AccountSage,
    AxeSage,
    SectionSage,
    VatRegimeSage,
    VatSage,
    VatRatSage,
    PaymentCondition,
    TabDivSage,
    CategorySage,
    CurrencySage,
)


class AccountSageForm(forms.ModelForm):
    """Validation de l'import ZBIACCOUNT des comptes comptables Sage X3"""

    collective = SageNullBooleanField()
    analytic = SageNullBooleanField()

    class Meta:
        """class Meta du forms.ModelForm django"""

        model = AccountSage
        fields = [
            "code_plan_sage",
            "account",
            "name",
            "short_name",
            "collective",
            "call_code",
            "analytic",
            "nb_axes",
            "axe_00",
            "section_00",
            "axe_01",
            "section_01",
            "axe_02",
            "section_02",
            "axe_03",
            "section_03",
            "axe_04",
            "section_04",
            "axe_05",
            "section_05",
            "axe_06",
            "section_06",
            "axe_07",
            "section_07",
            "axe_08",
            "section_08",
            "axe_09",
            "section_09",
            "vat_default",
            "chargeback_x3",
            "bu_suc",
        ]


class AxeSageForm(forms.ModelForm):
    """Validation de l'import ZBIAXES des Axes Sage X3"""

    class Meta:
        """class Meta du forms.ModelForm django"""

        model = AxeSage
        fields = [
            "axe",
            "name",
        ]


class SectionSageForm(forms.ModelForm):
    """Validation de l'import ZBICCE des Sections Sage X3"""

    chargeable = SageNullBooleanField()

    class Meta:
        """class Meta du forms.ModelForm django"""

        model = SectionSage
        fields = [
            "axe",
            "section",
            "chargeable",
            "regroup_01",
            "regroup_02",
        ]


class VatRegimeSageForm(forms.ModelForm):
    """Validation de l'import ZBIVAT des Régimes de TVA Sage X3"""

    class Meta:
        """class Meta du forms.ModelForm django"""

        model = VatRegimeSage
        fields = [
            "vat_regime",
            "flag_active",
            "name",
            "short_name",
            "vat_code",
            "sale_class",
            "regime_type",
        ]


class VatSageForm(forms.ModelForm):
    """Validation de l'import ZBIRATVAT des TVA Sage X3"""

    class Meta:
        """class Meta du forms.ModelForm django"""

        model = VatSage
        fields = [
            "vat",
            "name",
            "vat_regime",
        ]


class VatRatSageForm(forms.ModelForm):
    """Validation de l'import ZBIRATVAT des Taux de TVA Sage X3"""

    exoneration = SageNullBooleanField()
    vat_start_date = forms.DateField(input_formats=["%d%m%y"])

    class Meta:
        """class Meta du forms.ModelForm django"""

        model = VatRatSage
        fields = [
            "vat",
            "vat_start_date",
            "rate",
            "exoneration",
        ]


class PaymentConditionForm(forms.ModelForm):
    """Validation de l'import ZBIPTE des Conditions de paiement Sage X3"""

    class Meta:
        """class Meta du forms.ModelForm django"""

        model = PaymentCondition
        fields = [
            "code",
            "name",
            "short_name",
        ]


class TabDivSageForm(forms.ModelForm):
    """Validation de l'import ZBIDIV des Tables Diverses Sage X3"""

    def_val = SageNullBooleanField()
    flag_active = SageNullBooleanField()

    class Meta:
        """class Meta du forms.ModelForm django"""

        model = TabDivSage
        fields = [
            "num_table",
            "code",
            "a_01",
            "a_02",
            "a_03",
            "a_04",
            "a_05",
            "a_06",
            "a_07",
            "a_08",
            "a_09",
            "a_10",
            "a_11",
            "a_12",
            "a_13",
            "a_14",
            "a_15",
            "n_01",
            "n_02",
            "n_03",
            "n_04",
            "n_05",
            "n_06",
            "n_07",
            "n_08",
            "n_09",
            "n_10",
            "n_11",
            "n_12",
            "n_13",
            "n_14",
            "n_15",
            "name",
            "short_name",
            "flag_active",
        ]


class CategorySageForm(forms.ModelForm):
    """Validation de l'import ZBICATC des Catégories Sage X3"""

    class Meta:
        """class Meta du forms.ModelForm django"""

        model = CategorySage
        fields = [
            "initial",
            "code",
            "name",
            "short_name",
            "cur",
        ]


class CurrencySageForm(forms.ModelForm):
    """Validation de l'import ZBICUR des Taux de Change Sage X3"""

    exchange_date = forms.DateField(input_formats=["%d%m%y"])
    modification_date = forms.DateField(input_formats=["%d%m%y"])

    class Meta:
        """class Meta du forms.ModelForm django"""

        model = CurrencySage
        fields = [
            "currency_current",
            "currency_change",
            "exchange_date",
            "exchange_type",
            "exchange_rate",
            "exchange_inverse",
            "divider",
            "modification_date",
        ]
