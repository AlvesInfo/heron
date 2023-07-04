import pendulum
from django.db import connection
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect, reverse

from heron.loggers import LOGGER_VIEWS
from apps.core.functions.functions_postgresql import query_file_dict_cursor
from apps.core.bin.change_traces import trace_change
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.validation_purchases.excel_outputs.excel_refac_cct import (
    excel_refac_cct,
)
from apps.edi.models import EdiValidation
from apps.validation_purchases.forms import RefacCctValidationForm


# CONTROLES ETAPE 5.1 - Contrôle Fournisseurs M vs M-1


def zsuppliers_m_purchases(request):
    """View de l'étape 5.1 - Contrôle Fournisseurs M vs M-1"""
    with connection.cursor() as cursor:
        sql_context_file = "apps/validation_purchases/sql_files/sql_suppliers_m_vs_m1.sql"
        elements = query_file_dict_cursor(cursor, file_path=sql_context_file)
        mois_dict = {}
        mois = 4

        for i in range(6, 10):
            mois_dict[f"M{mois-1}"] = (
                (
                    pendulum.now()
                    .subtract(months=mois)
                    .start_of("month")
                    .format("MMMM YYYY", locale="fr")
                )
                .capitalize()
                .replace(" ", "<br>")
            )
            mois -= 1

        context = {
            "titre_table": "5.1 - Contrôle Fournisseurs M vs M-1",
            "suppliers_validation": EdiValidation.objects.filter(final=False).first(),
            "clients": elements,
            "mois_dict": mois_dict,
        }

    return render(
        request, "validation_purchases/refac_cct.html", context=context
    )


def zsuppliers_m_purchases_export(request):
    """Export Excel du Contrôle Fournisseurs M vs M-1
    :param request: Request Django
    :return: response_file"""
    try:
        if request.method == "GET":
            today = pendulum.now()
            file_name = (
                "CONTROLE_FOURNISSEUR_M_VS_M-1_" f"{today.format('Y_M_D')}{today.int_timestamp}.xlsx"
            )

            return response_file(
                excel_refac_cct,
                file_name,
                CONTENT_TYPE_EXCEL,
            )

    except:
        LOGGER_VIEWS.exception("view : refac_cct_purchases_export")

    return redirect(reverse("validation_purchases:refac_cct_purchases"))
