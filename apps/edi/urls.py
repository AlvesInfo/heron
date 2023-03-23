from django.urls import path

from apps.edi.views import (
    import_edi_invoices,
    create_invoice_marchandises,
    create_post_invoices,
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
        create_invoice_marchandises,
        name="create_invoice_marchandise",
    ),
    path(
        "create_post_invoices/",
        create_post_invoices,
        name="create_post_invoices",
    ),
]
