"""Routes URL de l'application edi."""

from django.urls import path

from apps.edi.views import (
    create_hand_invoices,
    # IMPORTS
    import_edi_invoices,
    # JAUGES
    import_jauge,
)

app_name = "apps.edi"

urlpatterns = [
    # Intégration factures EDI
    *[
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
    ],
    # Jauges des intégrations
    *[
        path(
            "import_jauge/",
            import_jauge,
            name="import_jauge",
        ),
    ],
]
