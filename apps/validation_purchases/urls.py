from django.urls import path

from apps.validation_purchases.views import (
    integration_purchases,
    integration_purchases_export,
    integration_supplier_purchases,
    integration_supplier_purchases_export,
    details_purchases,
    details_purchases_export,
    without_cct_purchases,
    without_cct_purchases_export,
    families_invoices_purchases,
    families_invoices_purchases_export,
    articles_families_invoices_purchases,
    articles_families_invoices_purchases_export,
    balance_suppliers_purchases,
    balance_suppliers_purchases_export,
    invoices_suppliers_purchases,
    invoices_suppliers_purchases_export,

    rfa_cct_invoices_purchases,
    rfa_cct_invoices_purchases_export,
    rfa_prj_invoices_purchases,
    rfa_prj_invoices_purchases_export,

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
        # Intégration
        path(
            "integration_purchases/",
            integration_purchases,
            name="integration_purchases",
        ),
        path(
            "integration_purchases_export/",
            integration_purchases_export,
            name="integration_purchases_export",
        ),
        # Listing
        path(
            "integration_supplier_purchases/<third_party_num>/<big_category>/<month>/",
            integration_supplier_purchases,
            name="integration_supplier_purchases",
        ),
        path(
            "integration_supplier_purchases_export/",
            integration_supplier_purchases_export,
            name="integration_supplier_purchases_export",
        ),
        # Détails facture
        path(
            "details_purchases/<third_party_num>/<invoice_number>/",
            details_purchases,
            name="details_purchases",
        ),
        path(
            "details_purchases_export/",
            details_purchases_export,
            name="details_purchases_export",
        ),
        # Factures sans cct
        path(
            "without_cct_purchases/",
            without_cct_purchases,
            name="without_cct_purchases",
        ),
        path(
            "without_cct_purchases_export/",
            without_cct_purchases_export,
            name="without_cct_purchases_export",
        ),
        # Familles des Factures
        path(
            "families_invoices_purchases/",
            families_invoices_purchases,
            name="families_invoices_purchases",
        ),
        path(
            "families_invoices_purchases_export/",
            families_invoices_purchases_export,
            name="families_invoices_purchases_export",
        ),
        # Articles/Familles des Factures
        path(
            "articles_families_invoices_purchases/",
            articles_families_invoices_purchases,
            name="articles_families_invoices_purchases",
        ),
        path(
            "articles_families_invoices_purchases_export/",
            articles_families_invoices_purchases_export,
            name="articles_families_invoices_purchases_export",
        ),
        # Soldes
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
        # Factures
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
    # MENU CONTROLES RFA
    *[
        # par CCT
        path(
            "rfa_cct_invoices_purchases/",
            rfa_cct_invoices_purchases,
            name="rfa_cct_invoices_purchases",
        ),
        path(
            "rfa_cct_invoices_purchases_export/",
            rfa_cct_invoices_purchases_export,
            name="rfa_cct_invoices_purchases_export",
        ),
        # par PRJ
        path(
            "rfa_prj_invoices_purchases/",
            rfa_prj_invoices_purchases,
            name="rfa_prj_invoices_purchases",
        ),
        path(
            "rfa_prj_invoices_purchases_export/",
            rfa_prj_invoices_purchases_export,
            name="rfa_prj_invoices_purchases_export",
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
