from django.urls import path

from apps.edi.views import (
    import_edi_invoices,
    create_hand_invoices,
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
        "create_hand_invoices/<str:category>/",
        create_hand_invoices,
        name="create_hand_invoices",
    ),
]
