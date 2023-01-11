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
from apps.centers_clients.models import Maison
from apps.accountancy.models import VatSage
from apps.countries.models import Currency
from apps.edi.models import EdiImport
from apps.parameters.models import Category

INVOICES_CREATE_FIELDS = (
    "third_party_num",
    "invoice_number",
    "invoice_date",
    "invoice_type",
    "devise",
    "reference_article",
    "libelle",
    "qty",
    "net_unit_price",
    "client_name",
    "serial_number",
    "big_category",
    "created_by",
    "vat",
    "cct_uuid_identification",
    "unity",
    "manual_entry",
    "purchase_invoice",
    "sale_invoice",
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
            label="Tiers X3",
            required=True,
        )
        self.fields["third_party_num"] = third_party_num

        # CCT X3 ===================================================================================
        self.cct_choices = [("", "")] + [
            (
                maison.uuid_identification,
                f"{maison.cct}-" f"{maison.intitule}-" f"{maison.adresse[:50]}-" f"{maison.ville}",
            )
            for maison in Maison.objects.all()
        ]
        cct_uuid_identification = forms.ChoiceField(
            choices=self.cct_choices,
            label="CCT X3",
            required=True,
        )
        self.fields["cct_uuid_identification"] = cct_uuid_identification

        # TYPE FACTURE FAF / AVO ===================================================================
        self.invoice_type_choices = [("380", "FAF"), ("381", "AVO")]
        invoice_type = forms.ChoiceField(
            choices=self.invoice_type_choices,
            label="Type de Facture",
            required=True,
        )
        self.fields["invoice_type"] = invoice_type

        # DEVISE ===================================================================================
        self.devise_choices = [
            (currency.code, currency.code) for currency in Currency.objects.all().order_by("code")
        ]
        devise = forms.ChoiceField(
            choices=self.devise_choices, label="Devise", required=True, initial="EUR"
        )
        self.fields["devise"] = devise

        # SENS ACHAT ou VENTE ou ACHAT/VENT ========================================================
        self.sens_choices = [(0, "AC"), (1, "VE"), (2, "AC/VE")]
        sens = forms.ChoiceField(
            choices=self.sens_choices, label="Sens", required=True, initial="AC/VE"
        )
        self.fields["sens"] = sens

        # ARTICLE FOURNISSEUR ======================================================================
        self.sens_choices = [(0, "AC"), (1, "VE"), (2, "AC/VE")]
        sens = forms.ChoiceField(
            choices=self.sens_choices, label="Sens", required=True, initial="AC/VE"
        )
        self.fields["sens"] = sens

        # TVA ======================================================================================
        self.vat_choices = [(vat.vat, vat.vat) for vat in VatSage.objects.all()]
        vat = forms.ChoiceField(choices=self.vat_choices, label="TVA", required=True, initial="001")
        self.fields["vat"] = vat

        # ==========================================================================================
        self.fields["big_category"] = forms.UUIDField(
            initial=Category.objects.get(slug_name="marchandises").uuid_identification
        )
        self.fields["manual_entry"] = forms.BooleanField(initial=True)

    class Meta:
        """class Meta"""

        model = EdiImport
        fields = INVOICES_CREATE_FIELDS
