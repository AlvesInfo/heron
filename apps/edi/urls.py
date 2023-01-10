from django.urls import path

from apps.edi.views import (
    import_edi_invoices,
    invoice_marchandise_create,
)

app_name = "apps.edi"

urlpatterns = [
    # Intégration factures EDI
    path(
        "import_edi_invoices/",
        import_edi_invoices,
        name="import_edi_invoices",
    ),
    # Saisie Facture de marchandise
    path(
        "create_invoice_marchandise/",
        invoice_marchandise_create,
        name="create_invoice_marchandise",
    ),
]
