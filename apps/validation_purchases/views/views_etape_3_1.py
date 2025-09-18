import pendulum
from django.contrib import messages
from django.db import connection
from django.shortcuts import render, redirect, reverse
from django.http import JsonResponse
from django.db.models import Q

from heron.loggers import LOGGER_VIEWS
from apps.core.bin.change_traces import trace_change
from apps.core.functions.functions_postgresql import query_file_dict_cursor
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.validation_purchases.excel_outputs.excel_integration_invoices_familly import (
    excel_integration_invoices_familly,
)
from apps.validation_purchases.excel_outputs.excel_supplier_details_invoices_familly import (
    excel_supplier_details_invoice,
)
from apps.edi.models import EdiValidation
from apps.validation_purchases.forms import FamiliesValidationForm

# CONTROLES ETAPE 3.1 - CONTROLE FAMILLES


def families_invoices_purchases(request):
    """View de l'étape 3.1 des écrans de contrôles"""
    sql_context_file = "apps/validation_purchases/sql_files/sql_families_invoices.sql"

    with connection.cursor() as cursor:
        invoices_famillies = query_file_dict_cursor(
            cursor,
            file_path=sql_context_file,
        )
        context = {
            "titre_table": "3.1 - Contrôle des familles - Achats",
            "invoices_famillies": invoices_famillies,
            "nb_paging": 100,
            "family_validation": EdiValidation.objects.filter(
                Q(final=False) | Q(final__isnull=True)
            ).first(),
        }

        return render(
            request, "validation_purchases/families_invoices_suppliers.html", context=context
        )


def families_invoices_purchases_export(request):
    """Export Excel de
    :param request: Request Django
    :return: response_file"""
    try:
        if request.method == "GET":
            today = pendulum.now()
            file_name = (
                "FACTURES_CONTROLE_FAMILLES_" f"{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"
            )

            return response_file(
                excel_integration_invoices_familly,
                file_name,
                CONTENT_TYPE_EXCEL,
            )

    except:
        LOGGER_VIEWS.exception("view : families_invoices_purchases_export")

    return redirect(reverse("validation_purchases:families_invoices_purchases"))


def supplier_details_invoices_purchases_export(request, third_party_num):
    """Export Excel de
    :param request: Request Django
    :param third_party_num: Tiers X3
    :return: response_file"""
    try:
        if request.method == "GET":
            today = pendulum.now()
            file_name = (
                f"FACTURES_CONTROLE_FAMILLES_{third_party_num}_"
                f"{today.format('Y_M_D')}{today.int_timestamp}.xlsx"
            )
            attr_dict = {"third_party_num": third_party_num}

            return response_file(
                excel_supplier_details_invoice,
                file_name,
                CONTENT_TYPE_EXCEL,
                attr_dict,
            )

    except:
        LOGGER_VIEWS.exception("view : supplier_details_invoices_purchases_export")

    return redirect(reverse("validation_purchases:families_invoices_purchases"))


def families_validation(request):
    """Validation de l'écran de contrôle des familles d'achat"""

    if not request.is_ajax() and request.method != "POST":
        return redirect("home")

    level = 50
    request.session["level"] = 50
    message = "Il y a eu une erreur pendant la validation"
    data = {"success": "ko"}

    form = FamiliesValidationForm(request.POST or None)

    if form.is_valid():
        try:
            uuid_identification = form.cleaned_data.get("uuid_identification")
            families_after = form.cleaned_data.get("families", False)
            before_kwargs = {
                "uuid_identification": uuid_identification,
            }
            update_kwargs = {
                "uuid_identification": uuid_identification,
                "families": families_after,
            }
            trace_change(request, EdiValidation, before_kwargs, update_kwargs)

            if families_after:
                request.session["level"] = 20
                message = "Le contrôle des familles est maintenant validé"
                data["success"] = "ok"
            else:
                request.session["level"] = 50
                message = "Le contrôle des familles est maintenant invalidé"

        except:
            LOGGER_VIEWS.exception(f"Views : families_validation error : {form.cleaned_data!r}")

    else:
        LOGGER_VIEWS.exception(f"Views : families_validation error, form invalid : {form.errors!r}")

    messages.add_message(request, level, message)

    return JsonResponse(data)
