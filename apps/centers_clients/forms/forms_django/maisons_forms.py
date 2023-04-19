# pylint: disable=E0401,R0903
"""
Forms des Maisons
"""
from django import forms
from django.forms import CheckboxInput
from apps.parameters.forms.forms_django.const_forms import SELECT_FLUIDE_DICT, CHECK_BOX_DICT
from apps.book.models import Society
from apps.accountancy.models import CctSage
from apps.centers_clients.models import (
    Maison,
    MaisonBi,
    MaisonSupllierExclusion,
    SupllierCountryExclusion,
)


class MaisonForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        """Ajout ou transformation des champs de formulaires"""
        super().__init__(*args, **kwargs)

        self.fields["code_maison"].required = False
        self.fields["code_cosium"].required = False
        self.fields["reference_cosium"].required = False
        self.fields["code_bbgr"].required = False

    class Meta:
        model = Maison
        fields = [
            "cct",
            "center_purchase",
            "sign_board",
            "intitule",
            "intitule_court",
            "client_familly",
            "code_maison",
            "code_cosium",
            "reference_cosium",
            "code_bbgr",
            "opening_date",
            "closing_date",
            "signature_franchise_date",
            "agreement_franchise_end_date",
            "agreement_renew_date",
            "entry_fee_amount",
            "renew_fee_amoount",
            "sale_price_category",
            "generic_coefficient",
            "immeuble",
            "adresse",
            "code_postal",
            "ville",
            "pays",
            "telephone",
            "mobile",
            "email",
            "third_party_num",
            "invoice_client_name",
            "sage_vat_by_default",
            "sage_plan_code",
            "currency",
            "language",
            "rfa_frequence",
            "rfa_remise",
            "credit_account",
            "debit_account",
            "prov_account",
            "extourne_account",
            "budget_code",
            "integrable",
            "chargeable",
            "od_ana",
            "axe_bu",
            "siren_number",
            "siret_number",
            "vat_cee_number"
        ]

        widgets = {
            "cct": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "third_party_num": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "pays": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "center_purchase": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "sign_board": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "client_familly": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "currency": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "language": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "sage_vat_by_default": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "sage_plan_code": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "rfa_frequence": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "rfa_remise": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "sale_price_category": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "credit_account": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "debit_account": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "prov_account": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "extourne_account": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "budget_code": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "axe_bu": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "od_ana": CheckboxInput(attrs=CHECK_BOX_DICT),
            "integrable": CheckboxInput(attrs=CHECK_BOX_DICT),
            "chargeable": CheckboxInput(attrs=CHECK_BOX_DICT),
        }


class MaisonImportForm(forms.ModelForm):
    class Meta:
        model = Maison
        fields = [
            "code_maison",
            "cct",
            "third_party_num",
            "intitule",
            "intitule_court",
            "code_cosium",
            "reference_cosium",
            "code_bbgr",
            "opening_date",
            "closing_date",
            "immeuble",
            "adresse",
            "code_postal",
            "ville",
            "pays",
            "telephone",
            "email",
            "sage_vat_by_default",
            "center_purchase",
            "sign_board",
            "integrable",
            "chargeable",
            "credit_account",
            "debit_account",
            "client_familly",
            "signature_franchise_date",
            "sage_plan_code",
        ]


class ImportMaisonBiForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.MAISONS_CHOICES = [("", "")] + [
            (maison.code_maison, f"{maison.code_maison}-{maison.intitule}")
            for maison in MaisonBi.objects.exclude(code_maison="0").order_by("code_maison")
        ]
        maison_bi = forms.ChoiceField(
            choices=self.MAISONS_CHOICES,
            label="Code Maison B.I",
            required=True,
        )
        self.fields["maison_bi"] = maison_bi

        self.CCT_CHOICES = [("", "")] + [
            (cct.cct, f"{cct.cct}-{cct.name}") for cct in CctSage.objects.order_by("cct")
        ]
        cct = forms.ChoiceField(
            choices=self.CCT_CHOICES,
            label="CCT X3",
            required=True,
        )
        self.fields["cct"] = cct

        self.TIERS_CHOICES = [("", "")] + [
            (tiers.third_party_num, f"{tiers.third_party_num}-{tiers.name}")
            for tiers in Society.objects.filter(is_client=True).order_by("third_party_num")
        ]
        tiers = forms.ChoiceField(
            choices=self.TIERS_CHOICES,
            label="Tiers X3",
            required=True,
        )
        self.fields["tiers"] = tiers


class MaisonSupllierExclusionForm(forms.ModelForm):
    """Formulaires des couples Tiers X3/Clients à écarter"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["third_party_num"].queryset = Society.objects.filter(in_use=True)

    class Meta:
        model = MaisonSupllierExclusion
        fields = [
            "third_party_num",
            "cct_uuid_identification",
        ]

        widgets = {
            "third_party_num": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "cct_uuid_identification": forms.Select(attrs=SELECT_FLUIDE_DICT),
        }


class MaisonSupllierExclusionDeleteForm(forms.ModelForm):
    """Formulaires des couples Tiers X3/Clients à supprimer"""

    class Meta:
        model = MaisonSupllierExclusion
        fields = [
            "id",
        ]


class SupllierCountryExclusionForm(forms.ModelForm):
    """Formulaires des couples Tiers X3/Pays Clients à écarter"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["third_party_num"].queryset = Society.objects.filter(in_use=True)

    class Meta:
        model = SupllierCountryExclusion
        fields = [
            "third_party_num",
            "pays",
        ]

        widgets = {
            "third_party_num": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "pays": forms.Select(attrs=SELECT_FLUIDE_DICT),
        }


class SupllierCountryExclusionDeleteForm(forms.ModelForm):
    """Formulaires des couples Tiers X3/Pays Clients à supprimer"""

    class Meta:
        model = SupllierCountryExclusion
        fields = [
            "id",
        ]
