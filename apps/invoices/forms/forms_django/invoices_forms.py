# pylint: disable=E0401
"""
Formulaires django pour les factures

Commentaire:

created at: 2023-07-07
created by: Paulo ALVES

modified at: 2023-07-07
modified by: Paulo ALVES
"""
from django import forms

from apps.parameters.forms.forms_django.const_forms import SELECT_FLUIDE_DICT
from apps.invoices.models import InvoiceCommonDetails


class InvoiceSearchForm(forms.ModelForm):
    """Pour le Filtre de recherche des factures"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        invoice_number__icontains = forms.CharField(
            label="N° Facture",
            required=False,
        )
        self.fields["invoice_number__icontains"] = invoice_number__icontains
        self.fields["invoice_number__icontains"].required = False

        self.fields["third_party_num"].required = False
        self.fields["invoice_year"].required = False
        self.fields["cct"].required = False

    class Meta:
        """class Meta django"""

        model = InvoiceCommonDetails
        fields = ("third_party_num", "invoice_year", "cct")
        widgets = {
            "third_party_num": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "cct": forms.Select(attrs=SELECT_FLUIDE_DICT),
        }
