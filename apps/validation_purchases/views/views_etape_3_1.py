import pendulum
from django.db import connection
from django.shortcuts import render, redirect, reverse

from heron.loggers import LOGGER_VIEWS
from apps.core.functions.functions_postgresql import query_file_dict_cursor
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.validation_purchases.excel_outputs.excel_integration_invoices_familly import (
    excel_integration_invoices_familly,
)

# CONTROLES ETAPE 3.1 - CONTROLE FAMILLES


def families_invoices_purchases(request):
    """View de l'étape 3.1 des écrans de contrôles"""
    sql_context_file = "apps/validation_purchases/sql_files/sql_families_invoices.sql"

    with connection.cursor() as cursor:
        invoices_famillies = query_file_dict_cursor(
            cursor,
            file_path=sql_context_file,
        )
        context = {
            "titre_table": "3.1 - Contrôle des familles - Achats",
            "invoices_famillies": invoices_famillies,
            "nb_paging": 100,
        }

        return render(
            request, "validation_purchases/families_invoices_suppliers.html", context=context
        )


def families_invoices_purchases_export(request):
    """Export Excel de
    :param request: Request Django
    :return: response_file"""
    try:
        if request.method == "GET":
            today = pendulum.now()
            file_name = (
                "FACTURES_CONTROLE_FAMILLES_" f"{today.format('Y_M_D')}{today.int_timestamp}.xlsx"
            )

            return response_file(
                excel_integration_invoices_familly,
                file_name,
                CONTENT_TYPE_EXCEL,
            )

    except:
        LOGGER_VIEWS.exception("view : families_invoices_purchases_export")

    return redirect(reverse("validation_purchases:families_invoices_purchases"))
