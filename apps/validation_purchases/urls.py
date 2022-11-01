from django.urls import path

from apps.validation_purchases.views import (
    balance_suppliers_purchases,
    balance_suppliers_purchases_export,
    invoices_suppliers_purchases,
    invoices_suppliers_purchases_export,

    sage_controls_globals_purchases,
    validation_purchases_export_globals,
    sage_controls_details_purchases,
    validation_purchases_export_details,
    sage_controls_familles_purchases,
    validation_purchases_export_familles,
)

app_name = "apps.validation_purchases"

urlpatterns = [
    # MENU CONTROLES ACHATS
    *[
        # Soldes Fournisseurs
        path(
            "balance_suppliers_purchases/",
            balance_suppliers_purchases,
            name="balance_suppliers_purchases",
        ),
        path(
            "balance_suppliers_purchases_export/",
            balance_suppliers_purchases_export,
            name="balance_suppliers_purchases_export",
        ),
        # Factures Fournisseurs
        path(
            "invoices_suppliers_purchases/",
            invoices_suppliers_purchases,
            name="invoices_suppliers_purchases",
        ),
        path(
            "invoices_suppliers_purchases_export/",
            invoices_suppliers_purchases_export,
            name="invoices_suppliers_purchases_export",
        ),
    ],
    # MENU CONTROLES SAGES
    *[
        path(
            "sage_controls_globals_purchases/",
            sage_controls_globals_purchases,
            name="sage_controls_globals_purchases",
        ),
        path(
            "validation_purchases_export_globals/",
            validation_purchases_export_globals,
            name="validation_purchases_export_globals",
        ),
        path(
            "sage_controls_details_purchases/",
            sage_controls_details_purchases,
            name="sage_controls_details_purchases",
        ),
        path(
            "validation_purchases_export_details/",
            validation_purchases_export_details,
            name="validation_purchases_export_details",
        ),
        path(
            "sage_controls_familles_purchases/",
            sage_controls_familles_purchases,
            name="sage_controls_familles_purchases",
        ),
        path(
            "validation_purchases_export_familles/",
            validation_purchases_export_familles,
            name="validation_purchases_export_familles",
        ),
    ],
]
