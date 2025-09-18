# ruff: noqa: E722
import pendulum
from django.shortcuts import render, redirect, reverse

from heron.loggers import LOGGER_VIEWS

from apps.core.functions.functions_http_response import (
    response_file,
    CONTENT_TYPE_EXCEL,
)
from apps.validation_purchases.excel_outputs.output_excel_rfa_mensuelles import (
    excel_rfa_mensuelles,
)

# CONTROLES ETAPE 6.1 - Contrôles des achats importés


def rfa_mensuelles(request):
    """View de l'étape 6.1 - Contrôle des RFA mensuelles générées"""
    context = {
        "titre_table": "6.1 - Export des RFA mensuelles générées",
    }

    return render(
        request, "validation_purchases/rfa_mensuelles_list.html", context=context
    )


def rfa_generated_export(_):
    """View de l'étape 6.1 - Export des RFA mensuelles générée
    Export Excel des RFA mensuelles générée
    :param _: Request Django
    :return: response_file
    """
    try:
        today = pendulum.now()
        file_name = f"RFA_MENSUELLES_{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"

        return response_file(excel_rfa_mensuelles, file_name, CONTENT_TYPE_EXCEL)

    except:
        LOGGER_VIEWS.exception("view : rfa_generated_export")

    return redirect(reverse(""))
