import pendulum
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect, reverse

from heron.loggers import LOGGER_VIEWS
from apps.core.bin.change_traces import trace_change
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.validation_purchases.excel_outputs.excel_subscriptions import (
    excel_subscriptions,
)
from apps.edi.models import EdiValidation
from apps.validation_purchases.forms import SubscriptionsValidationForm

# CONTROLES ETAPE 3.5 - Contrôle des Abonnements


def subscriptions_purchases(request):
    """View de l'étape 3.5 des écrans de contrôles"""
    context = {
        "titre_table": "3.5 - Contrôle des Abonnements",
        "subscriptions_validation": EdiValidation.objects.filter(final=False).first()
    }

    return render(
        request, "validation_purchases/subscriptions.html", context=context
    )


def subscriptions_purchases_export(request):
    """Export Excel du Contrôle des Abonnements
    :param request: Request Django
    :return: response_file"""
    try:
        if request.method == "GET":
            today = pendulum.now()
            file_name = (
                "CONTROLE_ABONNEMENTS_" f"{today.format('Y_M_D')}{today.int_timestamp}.xlsx"
            )

            return response_file(
                excel_subscriptions,
                file_name,
                CONTENT_TYPE_EXCEL,
            )

    except:
        LOGGER_VIEWS.exception("view : subscriptions_purchases_export")

    return redirect(reverse("validation_purchases:subscriptions_purchases"))


def subscriptions_validation(request):
    """Validation de l'écran de Contrôle des Abonnements"""

    if not request.is_ajax() and request.method != "POST":
        return redirect("home")

    level = 50
    request.session["level"] = 50
    message = "Il y a eu une erreur pendant la validation"

    data = {
        "success": "ko"
    }

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

        except:
            LOGGER_VIEWS.exception(f"Views : subscriptions_validation error : {form.cleaned_data!r}")

    else:
        LOGGER_VIEWS.exception(
            f"Views : subscriptions_validation error, form invalid : {form.errors!r}"
        )

    messages.add_message(request, level, message)

    return JsonResponse(data)
