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

from apps.parameters.models import UnitChoices
from apps.parameters.forms import NumberInput
from apps.parameters.forms.forms_django.const_forms import SELECT_FLUIDE_DICT
from apps.book.models import Society
from apps.countries.models import Currency
from apps.edi.models import EdiImport

INVOICES_CREATE_FIELDS = (
    "third_party_num",
    "cct_uuid_identification",
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
    "vat",
    "unit_weight",
    "purchase_invoice",
    "sale_invoice",
)


class CreateBaseInvoiceForm(forms.ModelForm):
    """Changer le Tiers X3 d'une intégration"""

    def __init__(self, *args, **kwargs):
        """Ajout ou transformation des champs de formulaires"""
        super().__init__(*args, **kwargs)

        # TIERS X3 =================================================================================
        self.third_party_num_choices = [("", "")] + [
            (
                society.get("third_party_num"),
                f"{society.get('third_party_num')} - {society.get('name')}",
            )
            for society in Society.objects.filter(in_use=True).values("third_party_num", "name")
        ]
        third_party_num = forms.ChoiceField(
            choices=self.third_party_num_choices,
            widget=forms.Select(attrs={"class": "ui fluid search dropdown"}),
            label="Fournisseur X3",
            required=True,
            error_messages={"required": "Le Fournisseur (TiersX3) est obligatoire"},
        )
        self.fields["third_party_num"] = third_party_num

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
            (currency.get("code"), currency.get("code"))
            for currency in Currency.objects.all().order_by("code").values("code")
        ]
        devise = forms.ChoiceField(
            choices=self.devise_choices,
            widget=forms.Select(attrs={"class": "ui fluid search dropdown"}),
            label="Devise",
            required=True,
            initial="EUR",
        )
        self.fields["devise"] = devise

        # SENS ACHAT ou VENTE ou ACHAT/VENTE =======================================================
        self.sens_choices = [(0, "AC"), (1, "VE"), (2, "AC/VE")]
        sens = forms.ChoiceField(
            choices=self.sens_choices,
            widget=forms.Select(attrs={"class": "ui fluid search dropdown"}),
            label="Sens",
            required=False,
            initial=2,
        )
        self.fields["sens"] = sens

        # AUTRE ====================================================================================
        self.fields["invoice_number"].required = False
        self.fields["invoice_date"].error_messages = {
            "required": "Une date de facture est obligatoire"
        }

    class Meta:
        """class Meta"""

        model = EdiImport
        fields = [
            "third_party_num",
            "invoice_number",
            "invoice_date",
            "invoice_type",
            "devise",
        ]


class CreateDetailsInvoiceForm(forms.ModelForm):
    """Changer le Tiers X3 d'une intégration"""

    def __init__(self, *args, **kwargs):
        """Ajout ou transformation des champs de formulaires"""
        super().__init__(*args, **kwargs)

        self.fields["vat"].initial = "001"
        self.fields["unit_weight"].initial = 1

    class Meta:
        """class Meta"""

        model = EdiImport
        fields = [
            "cct_uuid_identification",
            "reference_article",
            "libelle",
            "qty",
            "net_unit_price",
            "client_name",
            "serial_number",
            "vat",
            "unit_weight",
        ]
        widgets = {
            "cct_uuid_identification": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "reference_article": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "qty": NumberInput(attrs={"step": "1", "style": "text-align: right;"}),
            "net_unit_price": NumberInput(
                attrs={"step": "0.01", "min": 0, "style": "text-align: right;"}
            ),
            "unit_weight": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "vat": forms.Select(attrs=SELECT_FLUIDE_DICT),
        }


class CreateEdiImportInvoiceForm(forms.ModelForm):
    """Formulaire pour la créqtion des factures Dans Edi_Import"""

    def __init__(self, *args, **kwargs):
        """Ajout ou transformation des champs de formulaires"""
        super().__init__(*args, **kwargs)

        self.fields["sub_category"].required = False

    class Meta:
        """class Meta"""

        model = EdiImport
        fields = [
            "third_party_num",
            "invoice_number",
            "invoice_date",
            "invoice_type",
            "devise",
            "cct_uuid_identification",
            "reference_article",
            "libelle",
            "qty",
            "net_unit_price",
            "client_name",
            "serial_number",
            "vat",
            "unit_weight",
            "ean_code",
            "famille",
            "axe_bu",
            "axe_prj",
            "axe_pro",
            "axe_pys",
            "axe_rfa",
            "customs_code",
            "item_weight",
            "big_category",
            "sub_category",
            "libelle",
            "reference_article",
            "origin",
            "created_by",
            "saisie_by",
            "invoice_month",
            "invoice_year",
            "purchase_invoice",
            "sale_invoice",
            "gross_unit_price",
            "net_amount",
            "vat_rate",
            "vat_amount",
            "amount_with_vat",
            "vat_regime",
            "modified_by",
        ]

