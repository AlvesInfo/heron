# pylint: disable=E0401,R0903,W0702,W0613,W0201
"""
Views des Articles
"""
import pendulum
from django.shortcuts import render

from heron.loggers import LOGGER_EXPORT_EXCEL
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.validation_sales.excel_outputs.output_excel_sales_not_final import (
    excel_heron_sales_not_final,
)


# CONTROLES ETAPE 5 ================================================================================


def sage_controls_globals_sales(request):
    """View de l'étape 5.5 des écrans de contrôles"""
    context = {"titre_table": "Contrôle Intégration Sage X3 - Ventes"}
    return render(request, "validation_sales/sage_controls.html", context=context)


def invoices_sales_export_globals(request):
    """
    Export Excel des ventes Héron non finalisées
    :param request: Request Django
    :return: response_file
    """
    try:
        if request.method == "POST":
            today = pendulum.now()
            file_name = f"VENTES_A_FINALISER_{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"

            return response_file(excel_heron_sales_not_final, file_name, CONTENT_TYPE_EXCEL)

    except:
        LOGGER_EXPORT_EXCEL.exception("view : invoices_sales_export_globals")

    context = {"titre_table": f"VENTES HERON NON FINALISEES"}

    return render(request, "validation_sales/sage_heron_sales.html", context=context)


def sage_controls_details_sales(request):
    """View de l'étape 5.5 A des écrans de contrôles"""
    context = {"titre_table": "Contrôle Intégration Sage X3 - Ventes", "details": True}
    return render(request, "validation_sales/sage_controls.html", context=context)


def validation_sales_export_details(request):
    """View de l'étape 5.5 A des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(request, "validation_sales/sage_controls.html", context=context)


def sage_controls_familles_sales(request):
    """View de l'étape 5.5 B des écrans de contrôles"""
    context = {
        "titre_table": "Contrôle Intégration Sage X3 - Détails Ventes",
        "details_familles": True,
        "details": True,
    }
    return render(request, "validation_sales/sage_controls.html", context=context)


def validation_sales_export_familles(request):
    """View de l'étape 5.5 B des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(request, "validation_sales/sage_controls.html", context=context)


# CONTROLES ETAPE 5.3


def compare_turnover_sales(request):
    """View de l'étape 5.3 des écrans de contrôles"""
    context = {
        "titre_table": "Comparaison CA vs Ventes par maisons et famille de produit ",
    }
    return render(request, "validation_sales/compare_turnover_sales.html", context=context)


def compare_turnover_sales_export(request):
    """View de l'étape 5.3 des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(request, "validation_sales/compare_turnover_sales.html", context=context)


def compare_turnover_sales_details(request):
    """View de l'étape 5.3 A des écrans de contrôles"""
    context = {
        "titre_table": "Comparaison CA vs Ventes par maisons et famille de produit ",
        "details": True,
    }
    return render(request, "validation_sales/compare_turnover_sales.html", context=context)


def compare_turnover_sales_export_details(request):
    """View de l'étape 5.3 A des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(request, "validation_sales/compare_turnover_sales.html", context=context)


# CONTROLES ETAPE 5


def controls_cct_sales(request):
    """View de l'étape 5 des écrans de contrôles"""
    context = {
        "titre_table": "Contrôle refac M M-1 par CCT",
    }
    return render(request, "validation_sales/controls_cct_sales.html", context=context)


def controls_cct_sales_export(request):
    """View de l'étape 5 des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(request, "validation_sales/controls_cct_sales.html", context=context)


def controls_cct_sales_suppliers(request):
    """View de l'étape 5A des écrans de contrôles"""
    context = {
        "titre_table": f"Contrôle refac M M-1 Fournisseurs pour le CCT : {'AF001'}",
        "details": True,
    }
    return render(request, "validation_sales/controls_cct_sales.html", context=context)


def controls_cct_sales_suppliers_export(request):
    """View de l'étape 5A des écrans de contrôles"""
    context = {"titre_table": "Export Excel Détails"}
    return render(request, "validation_sales/controls_cct_sales.html", context=context)


def controls_cct_sales_suppliers_details(request):
    """View de l'étape 5B des écrans de contrôles"""
    context = {
        "titre_table": f"Détails des factures Fournisseurs pour le CCT : {'AF001'}",
        "details": True,
    }
    return render(request, "validation_sales/controls_cct_sales.html", context=context)


def controls_cct_sales_suppliers_details_export(request):
    """View de l'étape 5B des écrans de contrôles"""
    context = {"titre_table": "Export Excel Détails des factures Fournisseurs"}
    return render(request, "validation_sales/controls_cct_sales.html", context=context)
