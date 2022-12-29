# pylint: disable=E0401,R0903
"""
Forms des Maisons
"""
from django import forms

from apps.book.models import Society
from apps.accountancy.models import CctSage
from apps.centers_clients.models import Maison, MaisonBi


class MaisonForm(forms.ModelForm):
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
        ]


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
