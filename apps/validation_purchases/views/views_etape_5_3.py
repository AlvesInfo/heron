import pendulum
from django.db import connection
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect, reverse

from heron.loggers import LOGGER_VIEWS
from apps.core.functions.functions_postgresql import query_file_dict_cursor
from apps.core.bin.change_traces import trace_change
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.validation_purchases.excel_outputs.excel_ca_cct import (
    excel_ca_cct,
)
from apps.edi.models import EdiValidation
from apps.validation_purchases.forms import CaCctValidationForm

# CONTROLES ETAPE 5.3 - Contrôle CA Cosium / Ventes Héron


def ca_cct(request):
    """View de l'étape 5.3 - Contrôle CA Cosium / Ventes Héron"""
    with connection.cursor() as cursor:
        sql_context_file = "apps/validation_purchases/sql_files/sql_ca_cct.sql"
        elements = query_file_dict_cursor(cursor, file_path=sql_context_file)
        mois_dict = {}
        mois = 1

        for _ in range(1, 3):
            mois_dict[f"M{mois-1}"] = (
                pendulum.now()
                .subtract(months=mois)
                .start_of("month")
                .format("MMMM YYYY", locale="fr")
            ).upper()
            mois += 1

        context = {
            "titre_table": "5.3 - Contrôle CA Cosium / Ventes Héron",
            "ca_cct_validation": EdiValidation.objects.filter(final=False).first(),
            "clients": elements,
            "mois_dict": mois_dict,
        }

    return render(request, "validation_purchases/ca_cct.html", context=context)


def ca_cct_export(request):
    """Export Excel 5.3 - Contrôle CA Cosium / Ventes Héron
    :param request: Request Django
    :return: response_file"""
    try:
        if request.method == "GET":
            today = pendulum.now()
            file_name = "CONTROLE_CA_CCT_" f"{today.format('Y_M_D')}{today.int_timestamp}.xlsx"

            return response_file(
                excel_ca_cct,
                file_name,
                CONTENT_TYPE_EXCEL,
            )

    except:
        LOGGER_VIEWS.exception("view : ca_cct_export")

    return redirect(reverse("validation_purchases:ca_cct"))


def ca_cct_validation(request):
    """Validation de l'écran de Contrôle 5.3 - Contrôle CA Cosium / Ventes Héron"""

    if not request.is_ajax() and request.method != "POST":
        return redirect("home")

    level = 50
    request.session["level"] = 50
    message = "Il y a eu une erreur pendant la validation"

    data = {"success": "ko"}

    form = CaCctValidationForm(request.POST or None)

    if form.is_valid():
        try:
            uuid_identification = form.cleaned_data.get("uuid_identification")
            validation_ca_after = form.cleaned_data.get("validation_ca", False)
            before_kwargs = {
                "uuid_identification": uuid_identification,
            }
            update_kwargs = {
                "uuid_identification": uuid_identification,
                "validation_ca": validation_ca_after,
            }
            trace_change(request, EdiValidation, before_kwargs, update_kwargs)

            if validation_ca_after:
                request.session["level"] = 20
                message = "Le contrôle du CA Cosium / Ventes Héron est maintenant validé"
                data["success"] = "ok"
            else:
                request.session["level"] = 50
                message = "Le contrôle du CA Cosium / Ventes Héron est maintenant invalidé"

        except:
            LOGGER_VIEWS.exception(f"Views : ca_cct_validation error : {form.cleaned_data!r}")

    else:
        LOGGER_VIEWS.exception(f"Views : ca_cct_validation error, form invalid : {form.errors!r}")

    messages.add_message(request, level, message)

    return JsonResponse(data)
