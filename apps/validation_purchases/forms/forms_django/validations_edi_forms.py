# pylint: disable=E0401,R0903
"""
FR : Module des formulaires de validation des imports Sage X3
EN : Sage X3 import validation forms module

Commentaire:

created at: 2022-11-11
created by: Paulo ALVES

modified at: 2021-11-11
modified by: Paulo ALVES
"""
from django import forms

from apps.book.models import Society
from apps.edi.models import EdiImport, EdiImportControl


class EdiImportAllForm(forms.ModelForm):
    """Formulaire de base des factures founisseurs importées"""

    class Meta:
        """class Meta"""

        model = EdiImport
        fields = "__all__"


class EdiImportGetForm(forms.ModelForm):
    """Formulaire de base des factures founisseurs importées"""

    class Meta:
        """class Meta"""

        model = EdiImport
        fields = ["id"]


class EdiImportValidationForm(forms.ModelForm):
    """Formulaire pour l'update des factures founisseurs importées"""

    class Meta:
        """class Meta"""

        model = EdiImport
        fields = [
            "third_party_num",
            "big_category",
            "invoice_month",
        ]


class DeleteEdiForm(forms.ModelForm):
    """Formulaire pour delete un fournisseur de facture EdiImport"""

    class Meta:
        """class Meta"""

        model = EdiImport
        fields = [
            "third_party_num",
            "supplier",
            "invoice_month",
        ]


class DeleteInvoiceForm(forms.ModelForm):
    """Formulaire pour flagué en delete une ligne de facture EdiImport"""

    class Meta:
        """class Meta"""

        model = EdiImport
        fields = [
            "third_party_num",
            "invoice_number",
            "invoice_month",
        ]


class DeleteFieldForm(forms.ModelForm):
    """Formulaire pour flagué en delete toutes les lignes de facture EdiImport"""

    class Meta:
        """class Meta"""

        model = EdiImport
        fields = [
            "id",
            "third_party_num",
            "invoice_number",
            "invoice_month",
            "purchase_invoice",
        ]


class DeletePkForm(forms.Form):
    """Formulaire pour flagué en delete une ligne de facture EdiImport"""

    pk = forms.IntegerField()


class EdiImportControlForm(forms.ModelForm):
    """Formulaire pour l'update des factures founisseurs importées"""

    third_party_num = forms.CharField(max_length=15, required=False)
    invoice_month = forms.CharField(max_length=15, required=False)

    class Meta:
        """class Meta"""

        model = EdiImportControl
        fields = [
            "statement_without_tax",
            "statement_with_tax",
            "comment",
        ]


class UpdateSupplierPurchasesForm(forms.ModelForm):
    """Update du détail d'une facture"""

    class Meta:
        """class Meta"""

        model = EdiImport
        fields = ("id", "qty", "net_unit_price", "vat_rate")


class UpdateThirdpartynumForm(forms.ModelForm):
    """Changer le Tiers X3 d'une intégration"""

    def __init__(self, *args, **kwargs):
        """Ajout ou transformation des champs de formulaires"""
        super().__init__(*args, **kwargs)

        self.third_party_num_choices = [("", "")] + [
            (
                society.third_party_num,
                f"{society.third_party_num} - {society.name}",
            )
            for society in Society.objects.exclude(third_party_num__regex=r"^\d").filter(
                is_supplier=True
            )
        ]
        third_party_num = forms.ChoiceField(
            choices=self.third_party_num_choices,
            label="Tiers X3",
            required=True,
        )
        self.fields["third_party_num"] = third_party_num
        self.fields["uuid_identification"] = forms.UUIDField()

    class Meta:
        """class Meta"""

        model = EdiImport
        fields = ("flow_name", "supplier", "supplier_ident", "third_party_num")


class ControlValidationForm(forms.Form):
    """Form pour la validation"""

    uuid_identification = forms.UUIDField()
    valid = forms.BooleanField()

    def __init__(self, *args, **kwargs):
        """Ajout ou transformation des champs de formulaires"""
        super().__init__(*args, **kwargs)

        self.fields["valid"].required = False


class IntegrationValidationForm(forms.Form):
    """Validation des intégrations"""

    uuid_identification = forms.UUIDField()
    integration = forms.BooleanField()

    def __init__(self, *args, **kwargs):
        """Ajout ou transformation des champs de formulaires"""
        super().__init__(*args, **kwargs)

        self.fields["integration"].required = False


class FamiliesValidationForm(forms.Form):
    """Validation des intégrations"""

    uuid_identification = forms.UUIDField()
    families = forms.BooleanField()

    def __init__(self, *args, **kwargs):
        """Ajout ou transformation des champs de formulaires"""
        super().__init__(*args, **kwargs)

        self.fields["families"].required = False


class FranchiseursValidationForm(forms.Form):
    """Validation des intégrations"""

    uuid_identification = forms.UUIDField()
    franchiseurs = forms.BooleanField()

    def __init__(self, *args, **kwargs):
        """Ajout ou transformation des champs de formulaires"""
        super().__init__(*args, **kwargs)

        self.fields["franchiseurs"].required = False


class ClientsNewsValidationForm(forms.Form):
    """Validation des intégrations"""

    uuid_identification = forms.UUIDField()
    clients_news = forms.BooleanField()

    def __init__(self, *args, **kwargs):
        """Ajout ou transformation des champs de formulaires"""
        super().__init__(*args, **kwargs)

        self.fields["clients_news"].required = False


class SubscriptionsValidationForm(forms.Form):
    """Validation des intégrations"""

    uuid_identification = forms.UUIDField()
    subscriptions = forms.BooleanField()

    def __init__(self, *args, **kwargs):
        """Ajout ou transformation des champs de formulaires"""
        super().__init__(*args, **kwargs)

        self.fields["subscriptions"].required = False


class RfaValidationForm(forms.Form):
    """Validation des intégrations"""

    uuid_identification = forms.UUIDField()
    rfa = forms.BooleanField()

    def __init__(self, *args, **kwargs):
        """Ajout ou transformation des champs de formulaires"""
        super().__init__(*args, **kwargs)

        self.fields["rfa"].required = False


class RefacCctValidationForm(forms.Form):
    """Validation des intégrations"""

    uuid_identification = forms.UUIDField()
    refac_cct = forms.BooleanField()

    def __init__(self, *args, **kwargs):
        """Ajout ou transformation des champs de formulaires"""
        super().__init__(*args, **kwargs)

        self.fields["refac_cct"].required = False


class SuppliersValidationForm(forms.Form):
    """Validation des intégrations"""

    uuid_identification = forms.UUIDField()
    suppliers = forms.BooleanField()

    def __init__(self, *args, **kwargs):
        """Ajout ou transformation des champs de formulaires"""
        super().__init__(*args, **kwargs)

        self.fields["suppliers"].required = False


class CaCctValidationForm(forms.Form):
    """Validation des intégrations"""

    uuid_identification = forms.UUIDField()
    validation_ca = forms.BooleanField()

    def __init__(self, *args, **kwargs):
        """Ajout ou transformation des champs de formulaires"""
        super().__init__(*args, **kwargs)

        self.fields["validation_ca"].required = False
