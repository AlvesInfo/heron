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
import pendulum
from django import forms

from apps.book.models import Society
from apps.countries.models import Currency
from apps.edi.models import EdiImport
from apps.parameters.forms.forms_django.const_forms import DATE_INPUT


class CreateBaseMarchandiseForm(forms.ModelForm):
    """Formulaire d'entête pour la création des factures de Marchandises Dans Edi_Import"""

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
            widget=forms.Select(attrs={"class": "ui fluid search dropdown third_party_num"}),
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
        self.fields["invoice_date"].initial = (
            pendulum.now().start_of("month").subtract(days=1).date().isoformat()
        )

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

        widgets = {
            "invoice_date": forms.DateInput(attrs=DATE_INPUT)
        }


class CreateMarchandiseInvoiceForm(forms.ModelForm):
    """Formulaire des lignes pour la création des factures de Marchandises Dans Edi_Import"""

    def __init__(self, *args, **kwargs):
        """Ajout ou transformation des champs de formulaires"""
        super().__init__(*args, **kwargs)

        self.fields["sub_category"].required = False
        self.fields["delivery_number"].required = False
        self.fields["delivery_date"].required = False

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
            "delivery_number",
            "delivery_date",
            "vat_amount",
            "amount_with_vat",
        ]


class CreateBaseFormationForm(forms.ModelForm):
    """Formulaire d'entête pour la création des factures de Formation Dans Edi_Import"""

    def __init__(self, *args, **kwargs):
        """Ajout ou transformation des champs de formulaires"""
        super().__init__(*args, **kwargs)

        # TIERS X3 =================================================================================
        third_party_num = forms.CharField(
            initial="ZFORM",
            widget=forms.TextInput(
                attrs={"readonly": "", "style": "background-color: #efefff;font-weight: bold;"}
            ),
        )
        self.fields["third_party_num"] = third_party_num
        self.fields["third_party_num"].required = False

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

        # SENS ACHAT ou VENTE ou ACHAT/VENTE [(0, "AC"), (1, "VE"), (2, "AC/VE")] ==================
        sens = forms.CharField(
            initial=1,
            widget=forms.Select(attrs={"style": "display: none;"}),
            label="Sens",
            required=False,
        )
        self.fields["sens"] = sens

        # AUTRE ====================================================================================
        self.fields["invoice_number"].required = False
        self.fields["invoice_date"].error_messages = {
            "required": "Une date de facture est obligatoire"
        }
        self.fields["invoice_date"].initial = (
            pendulum.now().start_of("month").subtract(days=1).date().isoformat()
        )

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

        widgets = {
            "invoice_date": forms.DateInput(attrs=DATE_INPUT)
        }


class CreateFormationInvoiceForm(forms.ModelForm):
    """Formulaire des lignes pour la création des factures de Formation Dans Edi_Import"""

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
            "initial_date",
            "final_date",
            "libelle",
            "last_name",
            "first_name",
            "heures_formation",
            "formation_month",
            "vat_amount",
            "amount_with_vat",
        ]


class CreateBasePersonnelForm(forms.ModelForm):
    """Formulaire d'entête pour la création des factures de Personnel Dans Edi_Import"""

    def __init__(self, *args, **kwargs):
        """Ajout ou transformation des champs de formulaires"""
        super().__init__(*args, **kwargs)

        # TIERS X3 =================================================================================
        third_party_num = forms.CharField(
            initial="ZPERSONNEL",
            widget=forms.TextInput(
                attrs={"readonly": "", "style": "background-color: #efefff;font-weight: bold;"}
            ),
        )
        self.fields["third_party_num"] = third_party_num
        self.fields["third_party_num"].required = False

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

        # SENS ACHAT ou VENTE ou ACHAT/VENTE [(0, "AC"), (1, "VE"), (2, "AC/VE")] ==================
        sens = forms.CharField(
            initial=1,
            widget=forms.Select(attrs={"style": "display: none;"}),
            label="Sens",
            required=False,
        )
        self.fields["sens"] = sens

        # AUTRE ====================================================================================
        self.fields["invoice_number"].required = False
        self.fields["invoice_date"].error_messages = {
            "required": "Une date de facture est obligatoire"
        }
        self.fields["invoice_date"].initial = (
            pendulum.now().start_of("month").subtract(days=1).date().isoformat()
        )

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

        widgets = {"invoice_date": forms.DateInput(attrs=DATE_INPUT)}


class CreatePersonnelInvoiceForm(forms.ModelForm):
    """Formulaire des lignes pour la création des factures de Personnel Dans Edi_Import"""

    def __init__(self, *args, **kwargs):
        """Ajout ou transformation des champs de formulaires"""
        super().__init__(*args, **kwargs)

        self.fields["sub_category"].required = False
        self.fields["command_reference"].required = False
        self.fields["initial_date"].required = False
        self.fields["command_reference"].required = False

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
            "initial_date",
            "personnel_type",
            "command_reference",
        ]
