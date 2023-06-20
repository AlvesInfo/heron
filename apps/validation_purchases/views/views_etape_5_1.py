import pendulum
from django.shortcuts import render

from heron.loggers import LOGGER_EXPORT_EXCEL
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.validation_purchases.excel_outputs.output_excel_purchases_not_final import (
    excel_heron_purchases_not_final,
)


# CONTROLES ETAPE 5.1


def balance_suppliers_purchases(request):
    """View de l'étape 5.5 des écrans de contrôles"""
    context = {"titre_table": "Contrôle Soldes Fournisseurs - Achats"}
    return render(request, "validation_purchases/balance_suppliers.html", context=context)


def balance_suppliers_purchases_export(request):
    """View de l'étape 5.5 des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(request, "validation_purchases/balance_suppliers.html", context=context)


def invoices_suppliers_purchases(request):
    """View de l'étape 5.5 B des écrans de contrôles"""
    context = {"titre_table": "Contrôle Factures Fournisseurs - Achats"}
    return render(request, "validation_purchases/invoices_suppliers.html", context=context)


def invoices_purchases_export_globals(request):
    """View de l'étape 5.5 B des écrans de contrôles"""
    """
    Export Excel des achats Héron non finalisés
    :param request: Request Django
    :return: response_file
    """
    try:
        if request.method == "POST":
            today = pendulum.now()
            file_name = f"ACHATS_A_FINALISER_{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"

            return response_file(excel_heron_purchases_not_final, file_name, CONTENT_TYPE_EXCEL)

    except:
        LOGGER_EXPORT_EXCEL.exception("view : invoices_purchases_export_globals")

    context = {"titre_table": f"ACHATS HERON NON FINALISEES"}

    return render(request, "validation_purchases/sage_heron_purchases.html", context=context)
