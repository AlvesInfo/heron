# pylint: disable=E0401
# ruff: noqa: E722
"""
FR : View des lancements de la facturations
EN : View of invoicing launches

Commentaire:

created at: 2023-06-07
created by: Paulo ALVES

modified at: 2024-08-12
modified by: Paulo ALVES
"""

import pendulum
from django.shortcuts import render, redirect, reverse

from heron.loggers import LOGGER_VIEWS
from apps.core.functions.functions_http_response import (
    response_file,
    CONTENT_TYPE_EXCEL,
)
from apps.edi.models import EdiValidation
from apps.invoices.bin.export_csv_achats import get_achats


def valid_export_achats(request):
    """5.1 Vue d'export des achats non finalisés pour Eric Martinet"""
    titre_table = "EXPORT DES ACHATS AUX DATES DE LA DERNIERE FINALISATION VALIDE"
    context = {"margin_table": 50, "titre_table": titre_table}

    if request.method == "POST":
        return redirect(reverse("invoices:export_achats"))

    return render(request, "invoices/export_achats_invoices.html", context=context)


def export_achats(_):
    """
    Export du csv achats pour Eric Martinet
    :return:
    """
    try:
        today = pendulum.now()
        edi_validation = (
            EdiValidation.objects.filter(final=True).order_by("-id").first()
        )
        dte_d = pendulum.parse(edi_validation.billing_period.isoformat())
        dte_f = dte_d.last_of("month")
        file_name = (
            f"ACHATS_HERON_PERIOD_"
            f"{dte_d.format('Y_M_D')}_TO_{dte_f.format('Y_M_D')}_{today.int_timestamp}.csv"
        )
        return response_file(get_achats, file_name, CONTENT_TYPE_EXCEL, dte_d, dte_f)

    except:
        LOGGER_VIEWS.exception("view:export_achats")

    return redirect(reverse("invoices:export_achats"))
