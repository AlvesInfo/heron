import pendulum
from django.contrib import messages
from django.shortcuts import render, redirect, reverse
from django.http import JsonResponse
from django.db.models import Q

from heron.loggers import LOGGER_VIEWS
from apps.core.bin.change_traces import trace_change
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.validation_purchases.excel_outputs.excel_clients_news import (
    excel_clients_news,
)
from apps.edi.models import EdiValidation
from apps.validation_purchases.forms import ClientsNewsValidationForm

# CONTROLES ETAPE 3.3 - Contrôle nouveaux clients


def clients_news_purchases(request):
    """View de l'étape 3.3 des écrans de contrôles"""
    context = {
        "titre_table": "3.3 - Contrôle des nouveaux clients",
        "clients_news_validation": EdiValidation.objects.filter(
            Q(final=False) | Q(final__isnull=True)
        ).first(),
    }

    return render(request, "validation_purchases/clients_news.html", context=context)


def clients_news_purchases_export(request):
    """Export Excel du Contrôle des nouveaux clients
    :param request: Request Django
    :return: response_file"""
    try:
        if request.method == "GET":
            today = pendulum.now()
            file_name = (
                "CONTROLE_NOUVEAUX_CLIENTS_" f"{today.format('Y_M_D')}{today.int_timestamp}.xlsx"
            )

            return response_file(
                excel_clients_news,
                file_name,
                CONTENT_TYPE_EXCEL,
            )

    except:
        LOGGER_VIEWS.exception("view : cct_franchiseurs_purchases_export")

    return redirect(reverse("validation_purchases:cct_franchiseurs_purchases"))


def clients_news_validation(request):
    """Validation de l'écran de Contrôle des nouveaux clients"""

    if not request.is_ajax() and request.method != "POST":
        return redirect("home")

    level = 50
    request.session["level"] = 50
    message = "Il y a eu une erreur pendant la validation"
    data = {"success": "ko"}

    form = ClientsNewsValidationForm(request.POST or None)

    if form.is_valid():
        try:
            uuid_identification = form.cleaned_data.get("uuid_identification")
            clients_news_after = form.cleaned_data.get("clients_news", False)
            before_kwargs = {
                "uuid_identification": uuid_identification,
            }
            update_kwargs = {
                "uuid_identification": uuid_identification,
                "clients_news": clients_news_after,
            }
            trace_change(request, EdiValidation, before_kwargs, update_kwargs)

            if clients_news_after:
                request.session["level"] = 20
                message = "Le contrôle des nouveaux clients est maintenant validé"
                data["success"] = "ok"
            else:
                request.session["level"] = 50
                message = "Le contrôle des nouveaux clients est maintenant invalidé"

        except:
            LOGGER_VIEWS.exception(f"Views : clients_news_validation error : {form.cleaned_data!r}")

    else:
        LOGGER_VIEWS.exception(
            f"Views : clients_news_validation error, form invalid : {form.errors!r}"
        )

    messages.add_message(request, level, message)

    return JsonResponse(data)
