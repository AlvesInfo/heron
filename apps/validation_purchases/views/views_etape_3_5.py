"""Vues de l'étape 3.5 de la validation des achats : abonnements."""

import pendulum
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from apps.core.bin.change_traces import trace_change
from apps.core.functions.functions_http import is_ajax
from apps.core.functions.functions_http_response import CONTENT_TYPE_EXCEL, response_file
from apps.edi.models import EdiValidation
from apps.validation_purchases.excel_outputs.excel_subscriptions import (
    excel_subscriptions,
)
from apps.validation_purchases.forms import SubscriptionsValidationForm
from heron.loggers import LOGGER_VIEWS

# CONTROLES ETAPE 3.5 - Contrôle des Abonnements


def subscriptions_purchases(request):
    """View de l'étape 3.5 des écrans de contrôles."""
    context = {
        "titre_table": "3.5 - Contrôle des Abonnements",
        "subscriptions_validation": EdiValidation.objects.filter(
            Q(final=False) | Q(final__isnull=True)
        ).first(),
    }

    return render(request, "validation_purchases/subscriptions.html", context=context)


def subscriptions_purchases_export(request):
    """Export Excel du Contrôle des Abonnements.

    :param request: Request Django
    :return: response_file.
    """
    try:
        if request.method == "GET":
            today = pendulum.now()
            file_name = f"CONTROLE_ABONNEMENTS_{today.format('Y_M_D')}{today.int_timestamp}.xlsx"

            return response_file(
                excel_subscriptions,
                file_name,
                CONTENT_TYPE_EXCEL,
            )

    except Exception:
        LOGGER_VIEWS.exception("view : subscriptions_purchases_export")

    return redirect(reverse("validation_purchases:subscriptions_purchases"))


def subscriptions_validation(request):
    """Validation de l'écran de Contrôle des Abonnements."""
    if not is_ajax(request) or request.method != "POST":
        return redirect("home")

    level = 50
    request.session["level"] = 50
    message = "Il y a eu une erreur pendant la validation"

    data = {"success": "ko"}

    form = SubscriptionsValidationForm(request.POST or None)

    if form.is_valid():
        try:
            uuid_identification = form.cleaned_data.get("uuid_identification")
            subscriptions_after = form.cleaned_data.get("subscriptions", False)
            before_kwargs = {
                "uuid_identification": uuid_identification,
            }
            update_kwargs = {
                "uuid_identification": uuid_identification,
                "subscriptions": subscriptions_after,
            }
            trace_change(request, EdiValidation, before_kwargs, update_kwargs)

            if subscriptions_after:
                request.session["level"] = 20
                message = "Le contrôle des abonnements est maintenant validé"
                data["success"] = "ok"
            else:
                request.session["level"] = 50
                message = "Le contrôle des abonnements est maintenant invalidé"

        except Exception:
            LOGGER_VIEWS.exception("Views : subscriptions_validation error : %r", form.cleaned_data)

    else:
        LOGGER_VIEWS.error("Views : subscriptions_validation error, form invalid : %r", form.errors)

    messages.add_message(request, level, message)

    return JsonResponse(data)
