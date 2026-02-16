"""
Views des Validation des ventes par les fichiers génériques internes
"""
import pendulum
from django.shortcuts import render

from heron.loggers import LOGGER_EXPORT_EXCEL
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.validation_sales.excel_outputs.output_excel_sales_not_final_optimized import (
    excel_heron_sales_not_final,
)


# CONTROLES ETAPE 5.2 Contrôle Refacturation M/M-1 =================================================

def balance_internal_sales(request):
    """View de l'étape 5.2 Contrôle Refacturation M/M-1 (Ventes Internes)"""
    context = {"titre_table": "Contrôle des ventes Génériques (Ventes Internes)", "details": True}
    return render(request, "validation_sales/balance_internal_sales.html", context=context)


