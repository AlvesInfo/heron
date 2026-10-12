"""Vues de l'étape 3.6 de la validation des achats : contrôle des RFA de la période."""

import pendulum
from django.contrib import messages
from django.db import connection
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from apps.core.bin.change_traces import trace_change
from apps.core.functions.functions_http import is_ajax
from apps.core.functions.functions_http_response import CONTENT_TYPE_EXCEL, response_file
from apps.core.functions.functions_postgresql import query_file_dict_cursor
from apps.edi.models import EdiValidation
from apps.parameters.models import IconOriginChoice
from apps.validation_purchases.excel_outputs.excel_control_rfa_period import (
    control_rfa_period_excel,
)
from apps.validation_purchases.forms import RfaValidationForm
from heron.loggers import LOGGER_VIEWS

# CONTROLES ETAPE 3.6 - Contrôle période RFA


def control_rfa_period(request):
    """View de l'étape 3.6 - Contrôle période RFA."""
    with connection.cursor() as cursor:
        sql_context_file = "apps/validation_purchases/sql_files/sql_control_rfa_period.sql"
        elements = query_file_dict_cursor(cursor, file_path=sql_context_file)

        context = {
            "titre_table": "3.6 - Contrôle période RFA",
            "rfa_validation": EdiValidation.objects.filter(
                Q(final=False) | Q(final__isnull=True)
            ).first(),
            "rfa": elements,
            "legende": IconOriginChoice.objects.all(),
            "margin_table": 50,
            "margin_rep": 50,
            "nb_paging": 300,
        }

    return render(request, "validation_purchases/control_rfa_period.html", context=context)


def control_rfa_period_export(request):
    """Export Excel du Contrôle période RFA.

    :param request: Request Django
    :return: response_file.
    """
    try:
        if request.method == "GET":
            today = pendulum.now()
            file_name = f"CONTROLE_PERIODE_RFA{today.format('Y_M_D')}{today.int_timestamp}.xlsx"

            return response_file(
                control_rfa_period_excel,
                file_name,
                CONTENT_TYPE_EXCEL,
            )

    except Exception:
        LOGGER_VIEWS.exception("view : control_rfa_period_export")

    return redirect(reverse("validation_purchases:control_rfa_period"))


def control_rfa_period_validation(request):
    """Validation de l'écran de Contrôle 3.6 - Contrôle période RFA."""
    if not is_ajax(request) or request.method != "POST":
        return redirect("home")

    level = 50
    request.session["level"] = 50
    message = "Il y a eu une erreur pendant la validation"

    data = {"success": "ko"}

    form = RfaValidationForm(request.POST or None)

    if form.is_valid():
        try:
            uuid_identification = form.cleaned_data.get("uuid_identification")
            rfa_after = form.cleaned_data.get("rfa", False)
            before_kwargs = {
                "uuid_identification": uuid_identification,
            }
            update_kwargs = {
                "uuid_identification": uuid_identification,
                "rfa": rfa_after,
            }
            trace_change(request, EdiValidation, before_kwargs, update_kwargs)

            if rfa_after:
                request.session["level"] = 20
                message = "Le contrôle des périodes de RFA est maintenant validé"
                data["success"] = "ok"
            else:
                request.session["level"] = 50
                message = "Le contrôle des périodes de RFA est maintenant invalidé"

        except Exception:
            LOGGER_VIEWS.exception(
                "Views : control_rfa_period_validation error : %r", form.cleaned_data
            )

    else:
        LOGGER_VIEWS.error(
            "Views : control_rfa_period_validation error, form invalid : %r", form.errors
        )

    messages.add_message(request, level, message)

    return JsonResponse(data)
