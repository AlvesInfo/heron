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
from apps.invoices.models import SaleInvoice


class InvoiceSearchForm(forms.ModelForm):
    """Pour le Filtre de recherche des articles"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        reference_icontains = forms.CharField(
            label="Référence",
            required=False,
        )
        self.fields["reference__icontains"] = reference_icontains
        self.fields["reference__icontains"].required = False

        libelle_icontains = forms.CharField(
            label="Référence",
            required=False,
        )
        self.fields["libelle__icontains"] = libelle_icontains
        self.fields["libelle__icontains"].required = False

        libelle_heron_icontains = forms.CharField(
            label="Référence",
            required=False,
        )
        self.fields["libelle_heron__icontains"] = libelle_heron_icontains
        self.fields["libelle_heron__icontains"].required = False

        self.fields["third_party_num"].required = False
        self.fields["big_category"].required = False
        self.fields["sub_category"].required = False

    class Meta:
        """class Meta django"""

        model = SaleInvoice
        fields = ("third_party_num", "big_category", "sub_category")
        widgets = {
            "third_party_num": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "big_category": forms.Select(attrs=SELECT_FLUIDE_DICT),
            "sub_category": forms.Select(attrs=SELECT_FLUIDE_DICT),
        }
