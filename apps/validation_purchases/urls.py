from django.urls import path

from apps.validation_purchases.views import (
    # 2.1 Intégration
    integration_purchases,
    purchase_without_suppliers,
    purchase_without_suppliers_update,
    integration_supplier_validation,
    delete_supplier_edi_import,
    integration_purchases_export,
    alls_details_purchases_export,
    integration_validation,
    big_category_change,
    CreateIntegrationControl,
    UpdateIntegrationControl,
    # 2.1.A LISTING FACTURES
    integration_supplier_purchases,
    cct_change,
    delete_invoice_purchase,
    integration_supplier_purchases_export,
    # 2.1.B - DETAILS FACTURES
    details_purchase,
    delete_line_details_purchase,
    details_purchases_export,
    # 2.2 - FACTURES SANS CCT
    without_cct_purchases,
    without_cct_purchases_export,
    # 3.1 - FAMILLES ARTICLES
    families_invoices_purchases,
    families_invoices_purchases_export,
    supplier_details_invoices_purchases_export,
    families_validation,
    # 3.1 A - FAMILLES ARTICLES / FACTURES
    articles_families_invoices_purchases,
    articles_families_invoices_purchases_export,
    # 3.2 - CONTROLE CCT Franchiseurs
    cct_franchiseurs_purchases,
    cct_franchiseurs_purchases_export,
    franchiseurs_validation,
    # 3.3 - Nouveaux Clients
    clients_news_purchases,
    clients_news_purchases_export,
    clients_news_validation,
    # 3.5 - Abonnements
    subscriptions_purchases,
    subscriptions_purchases_export,
    subscriptions_validation,
    # 3.6 - Contrôle période RFA
    control_rfa_period,
    control_rfa_period_export,
    control_rfa_period_validation,
    # 5.0 - Contrôle Refac M M-1 par CCT
    refac_cct_purchases,
    refac_cct_purchases_export,
    refac_cct_validation,
    # 5.A - Contrôle Fournisseurs M vs M-1
    suppliers_m_purchases,
    suppliers_m_purchases_export,
    # 5.B - Contrôle Details Fournisseurs M vs M-1
    third_suppliers_m_purchases,
    third_suppliers_m_purchases_export,
    # 5.1 Fournisseurs M vs M-1
    balance_suppliers_purchases,
    balance_suppliers_purchases_export,
    balance_suppliers_purchases_validation,
    # 5.3 - Contrôle CA Cosium / Ventes Héron
    ca_cct,
    ca_cct_export,
    ca_cct_validation,
    # 5.3A - Contrôle CA Cosium / Ventes Héron par familles
    ca_familly_cct,
    ca_familly_cct_export,
    # 5.5
    invoices_purchases_export_globals,
    # 6.0 Export achats fournisseurs EDI
    suppliers_edi_purchases,
    edi_import_purchases_export,
    edi_import_purchases_export_csv,
    # RFA
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
    # 2.1 Intégration
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
            "integration_supplier_validation/",
            integration_supplier_validation,
            name="integration_supplier_validation",
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
            "alls_details_purchases_export/<str:enc_param>/",
            alls_details_purchases_export,
            name="alls_details_purchases_export",
        ),
        path(
            "integration_validation/",
            integration_validation,
            name="integration_validation",
        ),
    ],
    # 2.1.A LISTING FACTURES
    *[
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
            "integration_supplier_purchases_export/<str:flow_name>/<str:enc_param>/",
            integration_supplier_purchases_export,
            name="integration_supplier_purchases_export",
        ),
    ],
    # 2.1.B - DETAILS FACTURES
    *[
        path(
            "details_purchase/<str:flow_name>/<str:enc_param>/",
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
    ],
    # 2.2 - FACTURES SANS CCT
    *[
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
        path(
            "families_validation/",
            families_validation,
            name="families_validation",
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
    # 3.2 - CONTROLE CCT Franchiseurs
    *[
        path(
            "cct_franchiseurs_purchases/",
            cct_franchiseurs_purchases,
            name="cct_franchiseurs_purchases",
        ),
        path(
            "cct_franchiseurs_purchases_export/",
            cct_franchiseurs_purchases_export,
            name="cct_franchiseurs_purchases_export",
        ),
        path(
            "franchiseurs_validation/",
            franchiseurs_validation,
            name="franchiseurs_validation",
        ),
    ],
    # 3.3 - Nouveaux Clients
    *[
        path(
            "clients_news_purchases/",
            clients_news_purchases,
            name="clients_news_purchases",
        ),
        path(
            "clients_news_purchases_export/",
            clients_news_purchases_export,
            name="clients_news_purchases_export",
        ),
        path(
            "clients_news_validation/",
            clients_news_validation,
            name="clients_news_validation",
        ),
    ],
    # 3.5 - Abonnements
    *[
        path(
            "subscriptions_purchases/",
            subscriptions_purchases,
            name="subscriptions_purchases",
        ),
        path(
            "subscriptions_purchases_export/",
            subscriptions_purchases_export,
            name="subscriptions_purchases_export",
        ),
        path(
            "subscriptions_validation/",
            subscriptions_validation,
            name="subscriptions_validation",
        ),
    ],
    # 3.6 - Contrôle période RFA
    *[
        path(
            "control_rfa_period/",
            control_rfa_period,
            name="control_rfa_period",
        ),
        path(
            "control_rfa_period_export/",
            control_rfa_period_export,
            name="control_rfa_period_export",
        ),
        path(
            "control_rfa_period_validation/",
            control_rfa_period_validation,
            name="control_rfa_period_validation",
        ),
    ],
    # 6.0 Export achats fournisseurs EDI
    *[
        path(
            "suppliers_edi_purchases/",
            suppliers_edi_purchases,
            name="suppliers_edi_purchases",
        ),
        path(
            "edi_import_purchases_export/",
            edi_import_purchases_export,
            name="edi_import_purchases_export",
        ),
        path(
            "edi_import_purchases_export_csv/",
            edi_import_purchases_export_csv,
            name="edi_import_purchases_export_csv",
        ),
    ],
    # 5.0 - Contrôle Refac M M-1 par CCT
    *[
        path(
            "refac_cct_purchases/",
            refac_cct_purchases,
            name="refac_cct_purchases",
        ),
        path(
            "refac_cct_purchases_export/",
            refac_cct_purchases_export,
            name="refac_cct_purchases_export",
        ),
        path(
            "refac_cct_validation/",
            refac_cct_validation,
            name="refac_cct_validation",
        ),
    ],
    # 5.A - Contrôle Refac Fournisseurs M vs M-1
    *[
        path(
            "suppliers_m_purchases/<str:client>/",
            suppliers_m_purchases,
            name="suppliers_m_purchases",
        ),
        path(
            "suppliers_m_purchases_export/<str:client>/",
            suppliers_m_purchases_export,
            name="suppliers_m_purchases_export",
        ),
    ],
    # 5.B - Contrôle Refac Details Fournisseurs M vs M-1
    *[
        path(
            "third_suppliers_m_purchases/<str:client>/<str:third_party_num>/",
            third_suppliers_m_purchases,
            name="third_suppliers_m_purchases",
        ),
        path(
            "third_suppliers_m_purchases_export/<str:client>/<str:third_party_num>/",
            third_suppliers_m_purchases_export,
            name="third_suppliers_m_purchases_export",
        ),
    ],
    # 5.1 - Fournisseurs M vs M-1
    *[
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
            "balance_suppliers_purchases_validation/",
            balance_suppliers_purchases_validation,
            name="balance_suppliers_purchases_validation",
        ),
    ],
    # 5.3 - Contrôle CA Cosium / Ventes Héron
    *[
        path(
            "ca_cct/",
            ca_cct,
            name="ca_cct",
        ),
        path(
            "ca_cct_export/",
            ca_cct_export,
            name="ca_cct_export",
        ),
        path(
            "ca_cct_validation/",
            ca_cct_validation,
            name="ca_cct_validation",
        ),
    ],
    # 5.3A - Contrôle CA Cosium / Ventes Héron par familles
    *[
        path(
            "ca_familly_cct/<str:client>/",
            ca_familly_cct,
            name="ca_familly_cct",
        ),
        path(
            "ca_familly_cct_export/<str:client>/",
            ca_familly_cct_export,
            name="ca_familly_cct_export",
        ),
    ],
    # 5.5 -
    *[
        path(
            "invoices_purchases_export_globals/",
            invoices_purchases_export_globals,
            name="invoices_purchases_export_globals",
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
