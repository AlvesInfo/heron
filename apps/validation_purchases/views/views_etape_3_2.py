import pendulum
from django.contrib import messages
from django.shortcuts import render, redirect, reverse
from django.http import JsonResponse

from heron.loggers import LOGGER_VIEWS
from apps.core.bin.change_traces import trace_change
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.validation_purchases.excel_outputs.excel_cct_franchiseurs import (
    excel_cct_franchiseurs,
)
from apps.edi.models import EdiValidation
from apps.validation_purchases.forms import FranchiseursValidationForm

# CONTROLES ETAPE 3.2 - CONTROLE CCT Franchiseurs


def cct_franchiseurs_purchases(request):
    """View de l'étape 3.2 des écrans de contrôles"""
    context = {
        "titre_table": "3.2 - Contrôle des CCT/franchiseurs (MARK, INFO, etc…)",
        "franchiseurs_validation": EdiValidation.objects.filter(final=False).first(),
    }

    return render(request, "validation_purchases/cct_franchiseurs.html", context=context)


def cct_franchiseurs_purchases_export(request):
    """Export Excel du Contrôle des achats des CCT franchiseur (CAHA, MARK, INFO, etc…)
    :param request: Request Django
    :return: response_file"""
    try:
        if request.method == "GET":
            today = pendulum.now()
            file_name = (
                "CONTROLE_CCT_FFRANCHISEUR_" f"{today.format('Y_M_D')}{today.int_timestamp}.xlsx"
            )

            return response_file(
                excel_cct_franchiseurs,
                file_name,
                CONTENT_TYPE_EXCEL,
            )

    except:
        LOGGER_VIEWS.exception("view : cct_franchiseurs_purchases_export")

    return redirect(reverse("validation_purchases:cct_franchiseurs_purchases"))


def franchiseurs_validation(request):
    """Validation de l'écran de Contrôle des achats des CCT franchiseur"""

    if not request.is_ajax() and request.method != "POST":
        return redirect("home")

    level = 50
    request.session["level"] = 50
    message = "Il y a eu une erreur pendant la validation"
    data = {"success": "ko"}

    form = FranchiseursValidationForm(request.POST or None)

    if form.is_valid():
        try:
            uuid_identification = form.cleaned_data.get("uuid_identification")
            franchiseurs_after = form.cleaned_data.get("franchiseurs", False)
            before_kwargs = {
                "uuid_identification": uuid_identification,
            }
            update_kwargs = {
                "uuid_identification": uuid_identification,
                "franchiseurs": franchiseurs_after,
            }
            trace_change(request, EdiValidation, before_kwargs, update_kwargs)

            if franchiseurs_after:
                request.session["level"] = 20
                message = "Le contrôle des familles est maintenant validé"
                data["success"] = "ok"
            else:
                request.session["level"] = 50
                message = "Le contrôle des familles est maintenant invalidé"

        except:
            LOGGER_VIEWS.exception(f"Views : franchiseurs_validation error : {form.cleaned_data!r}")

    else:
        LOGGER_VIEWS.exception(
            f"Views : franchiseurs_validation error, form invalid : {form.errors!r}"
        )

    messages.add_message(request, level, message)

    return JsonResponse(data)
