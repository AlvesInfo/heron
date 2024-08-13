# pylint: disable=E0401
# ruff: noqa: E722
"""
FR : View des états de sorties
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


def finalize_purchases_export(request):
    """Vue d'export des achats finalisés avec filtres"""
    titre_table = "EXPORT DES ACHATS FINALISES"
    context = {"margin_table": 50, "titre_table": titre_table}
    try:
        if request.method == "POST":
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
        LOGGER_VIEWS.exception("invoices:finalize_purchases_export")

    return render(request, "invoices/export_achats_invoices.html", context=context)
