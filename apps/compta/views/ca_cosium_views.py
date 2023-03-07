# pylint: disable=E0401,W1203,W0703
"""
Views des Abonnements
"""
import pendulum
from django.shortcuts import render

from heron.loggers import LOGGER_VIEWS
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.periods.forms import MonthForm
from apps.compta.excel_outputs.output_excel_sales_cosium import excel_sales_cosium


def export_sales_cosium(request):
    """Export des ventes Cosium par périodes"""
    form = MonthForm(request.POST or None)

    try:

        if request.method == "POST" and form.is_valid():
            dte_d, dte_f = form.cleaned_data.get("periode").split("_")

            today = pendulum.now()
            file_name = (
                f"VENTES_COSIUM_{dte_d}_{dte_f}_"
                f"{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"
            )
            return response_file(
                excel_sales_cosium, file_name, CONTENT_TYPE_EXCEL, dte_d, dte_f
            )

    except Exception as error:
        print(error)
        LOGGER_VIEWS.exception(f"erreur form : {str(form.data)!r}")

    context = {
        "titre_table": "VENTES COSIUM PAR PERIODE",
        "form": form,
    }

    return render(request, "compta/export_sales_cosium.html", context=context)
