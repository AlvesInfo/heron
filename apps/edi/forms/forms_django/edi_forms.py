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
            "date_month",
        ]


class DeleteEdiForm(forms.ModelForm):
    """Formulaire pour delete un fournisseur de facture EdiImport"""

    class Meta:
        """class Meta"""

        model = EdiImport
        fields = [
            "third_party_num",
            "supplier",
            "big_category",
            "date_month",
            "delete",
        ]


class DeleteInvoiceForm(forms.ModelForm):
    """Formulaire pour flagué en delete une ligne de facture EdiImport"""

    class Meta:
        """class Meta"""

        model = EdiImport
        fields = [
            "third_party_num",
            "invoice_number",
            "date_month",
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
            "date_month",
            "delete",
        ]


class DeletePkForm(forms.Form):
    """Formulaire pour flagué en delete une ligne de facture EdiImport"""

    pk = forms.IntegerField()


class EdiImportControlForm(forms.ModelForm):
    """Formulaire pour l'update des factures founisseurs importées"""
    third_party_num = forms.CharField(max_length=15, required=False)
    date_month = forms.CharField(max_length=15, required=False)

    class Meta:
        model = EdiImportControl
        fields = [
            "statement_without_tax",
            "statement_with_tax",
            "comment",
        ]
