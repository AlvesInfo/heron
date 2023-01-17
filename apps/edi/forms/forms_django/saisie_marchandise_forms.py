# pylint: disable=E0401,R0903, E1101
"""
FR : Module de Formulaires pour le saisie de marchandises
EN : Forms module for entering goods

Commentaire:

created at: 2022-11-11
created by: Paulo ALVES

modified at: 2021-11-11
modified by: Paulo ALVES
"""
from django import forms

from apps.book.models import Society
from apps.accountancy.models import VatSage
from apps.countries.models import Currency
from apps.centers_clients.models import Maison
from apps.edi.models import EdiImport

INVOICES_CREATE_FIELDS = (
    "big_category",
    "sub_category",
    "third_party_num",
    "cct_uuid_identification",
    "invoice_number",
    "invoice_date",
    "invoice_type",
    "devise",
    "reference_article",
    "qty",
    "net_unit_price",
    "client_name",
    "serial_number",
    "vat",
    "unity",
)


class CreateInvoiceForm(forms.ModelForm):
    """Changer le Tiers X3 d'une intégration"""

    def __init__(self, *args, **kwargs):
        """Ajout ou transformation des champs de formulaires"""
        super().__init__(*args, **kwargs)

        # TIERS X3 =================================================================================
        self.third_party_num_choices = [("", "")] + [
            (
                society.third_party_num,
                f"{society.third_party_num} - {society.name}",
            )
            for society in Society.objects.filter(in_use=True)
        ]
        third_party_num = forms.ChoiceField(
            choices=self.third_party_num_choices,
            widget=forms.Select(attrs={"class": "ui fluid search dropdown"}),
            label="Tiers X3",
            required=True,
        )
        self.fields["third_party_num"] = third_party_num

        # CCT X3 ===================================================================================
        self.cct_choices = [("", "")] + [
            (
                maison.uuid_identification,
                f"{maison.cct}-" f"{maison.intitule}",
            )
            for maison in Maison.objects.all()
        ]
        cct_uuid_identification = forms.ChoiceField(
            choices=self.cct_choices,
            widget=forms.Select(attrs={"class": "ui fluid search dropdown"}),
            label="CCT X3",
            required=True,
        )
        self.fields["cct_uuid_identification"] = cct_uuid_identification

        # TYPE FACTURE FAF / AVO ===================================================================
        self.invoice_type_choices = [("380", "FAF"), ("381", "AVO")]
        invoice_type = forms.ChoiceField(
            choices=self.invoice_type_choices,
            widget=forms.Select(attrs={"class": "ui fluid search dropdown"}),
            label="Type de Facture",
            required=True,
        )
        self.fields["invoice_type"] = invoice_type

        # DEVISE ===================================================================================
        self.devise_choices = [
            (currency.code, currency.code) for currency in Currency.objects.all().order_by("code")
        ]
        devise = forms.ChoiceField(
            choices=self.devise_choices,
            widget=forms.Select(attrs={"class": "ui fluid search dropdown"}),
            label="Devise",
            required=True,
            initial="EUR",
        )
        self.fields["devise"] = devise

        # SENS ACHAT ou VENTE ou ACHAT/VENT ========================================================
        self.sens_choices = [(0, "AC"), (1, "VE"), (2, "AC/VE")]
        sens = forms.ChoiceField(
            choices=self.sens_choices,
            widget=forms.Select(attrs={"class": "ui fluid search dropdown"}),
            label="Sens",
            required=True,
            initial="AC/VE",
        )
        self.fields["sens"] = sens

        # TVA ======================================================================================
        self.vat_choices = [(vat.vat, vat.vat) for vat in VatSage.objects.all()]
        vat = forms.ChoiceField(
            choices=self.vat_choices,
            widget=forms.Select(attrs={"class": "ui fluid search dropdown"}),
            label="TVA X3",
            required=True,
            initial="001",
        )
        self.fields["vat"] = vat

    class Meta:
        """class Meta"""

        model = EdiImport
        fields = INVOICES_CREATE_FIELDS
        widgets = {
            "big_category": forms.Select(attrs={"class": "ui fluid search dropdown"}),
            "cct_uuid_identification": forms.Select(attrs={"class": "ui fluid search dropdown"}),
        }
