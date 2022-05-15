from django import forms

from apps.centers_clients.models import Maison


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
            "tiers",
            "invoice_client_name",
            "credit_account",
            "debit_account",
            "prov_account",
            "extourne_account",
            "sage_vat_by_default",
            "sage_plan_code",
            "rfa_frequence",
            "rfa_remise",
            "currency",
            "language",
        ]