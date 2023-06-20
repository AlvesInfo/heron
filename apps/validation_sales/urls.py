from django.urls import path

from .views import (
    # MENU CONTROLES VENTES
    compare_turnover_sales,
    compare_turnover_sales_export,
    compare_turnover_sales_details,
    compare_turnover_sales_export_details,
    controls_cct_sales_suppliers,
    controls_cct_sales_export,
    controls_cct_sales,
    controls_cct_sales_suppliers_export,
    controls_cct_sales_suppliers_details,
    controls_cct_sales_suppliers_details_export,
    # MENU CONTROLES SAGE
    sage_controls_globals_sales,
    invoices_sales_export_globals,
    sage_controls_details_sales,
    validation_sales_export_details,
    sage_controls_familles_sales,
    validation_sales_export_familles,
)

app_name = "apps.validation_sales"

urlpatterns = [
    # MENU CONTROLES VENTES
    *[
        # Intégration
        # Ventes vs CA
        path(
            "compare_turnover_sales/",
            compare_turnover_sales,
            name="compare_turnover_sales",
        ),
        path(
            "compare_turnover_sales_export/",
            compare_turnover_sales_export,
            name="compare_turnover_sales_export",
        ),
        path(
            "compare_turnover_sales_details/",
            compare_turnover_sales_details,
            name="compare_turnover_sales_details",
        ),
        path(
            "compare_turnover_sales_export_details/",
            compare_turnover_sales_export_details,
            name="compare_turnover_sales_export_details",
        ),
        # Ventes par CCT
        path(
            "controls_cct_sales/",
            controls_cct_sales,
            name="controls_cct_sales",
        ),
        path(
            "controls_cct_sales_export/",
            controls_cct_sales_export,
            name="controls_cct_sales_export",
        ),
        path(
            "controls_cct_sales_suppliers/",
            controls_cct_sales_suppliers,
            name="controls_cct_sales_suppliers",
        ),
        path(
            "controls_cct_sales_suppliers_export/",
            controls_cct_sales_suppliers_export,
            name="controls_cct_sales_suppliers_export",
        ),
        path(
            "controls_cct_sales_suppliers_details/",
            controls_cct_sales_suppliers_details,
            name="controls_cct_sales_suppliers_details",
        ),
        path(
            "controls_cct_sales_suppliers_details_export/",
            controls_cct_sales_suppliers_details_export,
            name="controls_cct_sales_suppliers_details_export",
        ),
    ],
    # MENU CONTROLES SAGE
    *[
        # Ventes Sage
        path(
            "sage_controls_globals_sales/",
            sage_controls_globals_sales,
            name="sage_controls_globals_sales",
        ),
        path(
            "invoices_sales_export_globals/",
            invoices_sales_export_globals,
            name="invoices_sales_export_globals",
        ),
        # Ventes Détails
        path(
            "sage_controls_details_sales/",
            sage_controls_details_sales,
            name="sage_controls_details_sales",
        ),
        path(
            "validation_sales_export_details/",
            validation_sales_export_details,
            name="validation_sales_export_details",
        ),
        # Ventes Famille
        path(
            "sage_controls_familles_sales/",
            sage_controls_familles_sales,
            name="sage_controls_familles_sales",
        ),
        path(
            "validation_sales_export_familles/",
            validation_sales_export_familles,
            name="validation_sales_export_familles",
        ),
    ],
]
