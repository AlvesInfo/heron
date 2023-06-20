from django.urls import path

from apps.validation_purchases.views import (
    integration_purchases,
    purchase_without_suppliers,
    purchase_without_suppliers_update,
    delete_supplier_edi_import,
    integration_purchases_export,
    big_category_change,
    CreateIntegrationControl,
    UpdateIntegrationControl,
    integration_supplier_purchases,
    cct_change,
    delete_invoice_purchase,
    integration_supplier_purchases_export,
    details_purchase,
    delete_line_details_purchase,
    details_purchases_export,
    without_cct_purchases,
    without_cct_purchases_export,
    # 3.1 - FAMILLES ARTICLES
    families_invoices_purchases,
    families_invoices_purchases_export,
    supplier_details_invoices_purchases_export,
    # 3.1 A - FAMILLES ARTICLES / FACTURES
    articles_families_invoices_purchases,
    articles_families_invoices_purchases_export,
    #
    balance_suppliers_purchases,
    balance_suppliers_purchases_export,
    invoices_suppliers_purchases,
    invoices_purchases_export_globals,
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
    # Intégration
    *[
        path(
            "integration_purchases/",
            integration_purchases,
            name="integration_purchases",
        ),
        path(
            "purchase_without_suppliers/",
            purchase_without_suppliers,
            name="purchase_without_suppliers",
        ),
        path(
            "purchase_without_suppliers_update/",
            purchase_without_suppliers_update,
            name="purchase_without_suppliers_update",
        ),
        path(
            "delete_supplier_edi_import/",
            delete_supplier_edi_import,
            name="delete_supplier_edi_import",
        ),
        path(
            "create_control/<str:enc_param>/",
            CreateIntegrationControl.as_view(),
            name="create_control",
        ),
        path(
            "update_control/<str:enc_param>/<int:pk>/",
            UpdateIntegrationControl.as_view(),
            name="update_control",
        ),
        path(
            "integration_purchases_export/",
            integration_purchases_export,
            name="integration_purchases_export",
        ),
        path(
            "big_category_change/",
            big_category_change,
            name="big_category_change",
        ),
        # Listing
        path(
            "integration_supplier_purchases/<str:enc_param>/",
            integration_supplier_purchases,
            name="integration_supplier_purchases",
        ),
        path(
            "cct_change/",
            cct_change,
            name="cct_change",
        ),
        path(
            "delete_invoice_purchase/",
            delete_invoice_purchase,
            name="delete_invoice_purchase",
        ),
        path(
            "integration_supplier_purchases_export/<str:enc_param>/",
            integration_supplier_purchases_export,
            name="integration_supplier_purchases_export",
        ),
        # Détails facture
        path(
            "details_purchase/<str:enc_param>/",
            details_purchase,
            name="details_purchase",
        ),
        path(
            "delete_line_details_purchase/",
            delete_line_details_purchase,
            name="delete_line_details_purchase",
        ),
        path(
            "details_purchases_export/<str:enc_param>/",
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
            "invoices_purchases_export_globals/",
            invoices_purchases_export_globals,
            name="invoices_purchases_export_globals",
        ),
    ],
    # 3.1 - FAMILLES ARTICLES
    *[
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
        path(
            "supplier_details_invoices_purchases_export/<str:third_party_num>/",
            supplier_details_invoices_purchases_export,
            name="supplier_details_invoices_purchases_export",
        ),
    ],
    # 3.1 A - FAMILLES ARTICLES / FACTURES
    *[
        path(
            "articles_families_invoices_purchases/<str:third_party_num>/",
            articles_families_invoices_purchases,
            name="articles_families_invoices_purchases",
        ),
        path(
            "articles_families_invoices_purchases_export/",
            articles_families_invoices_purchases_export,
            name="articles_families_invoices_purchases_export",
        ),
    ],
    # MENU CONTROLES RFA
    # par CCT
    *[
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
