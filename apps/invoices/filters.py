# pylint: disable=E0401,R0903
"""
Filtres pour des recherches dans les views
"""
import django_filters

from apps.invoices.models import InvoiceCommonDetails


class InvoiceFilter(django_filters.FilterSet):
    """Filtre des factures"""

    class Meta:
        """class Meta django"""

        model = InvoiceCommonDetails
        fields = {
            "third_party_num": ["exact"],
            "invoice_number": ["icontains"],
            "invoice_year": ["exact"],
            "cct": ["exact"],
        }
