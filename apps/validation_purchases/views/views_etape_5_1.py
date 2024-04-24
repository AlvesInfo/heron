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
from apps.validation_purchases.excel_outputs.excel_balance_suppliers_purchases import (
    excel_balance_suppliers_purchases,
)
from apps.edi.models import EdiValidation
from apps.validation_purchases.forms import SuppliersValidationForm


# CONTROLES ETAPE 5.1 Fournisseurs M vs M-1


def balance_suppliers_purchases(request):
    """View de l'étape 5.1 Fournisseurs M vs M-1"""
    sql_context_file = "apps/validation_purchases/sql_files/sql_suppliers_invoices_m_m1.sql"
    billing_period = (
        EdiValidation.objects.filter(Q(final=False) | Q(final__isnull=True)).first().billing_period
    )

    with connection.cursor() as cursor:
        invoices_suppliers = query_file_dict_cursor(
            cursor,
            file_path=sql_context_file,
            parmas_dict={"initial_date": billing_period},
        )

        start_date = pendulum.parse(billing_period.isoformat())

        mois_dict = {}

        for i in range(-3, 1):
            mois_dict[f"M{abs(i)}"] = (
                (start_date.add(months=i).start_of("month").format("MMMM YYYY", locale="fr"))
                .capitalize()
                .replace(" ", "<br>")
            )

        context = {
            "titre_table": "5.1 - Contrôle des fournisseurs M vs M-1",
            "invoices_suppliers": invoices_suppliers,
            "suppliers_validation": EdiValidation.objects.filter(
                Q(final=False) | Q(final__isnull=True)
            ).first(),
            "mois_dict": mois_dict,
        }

    return render(request, "validation_purchases/balance_suppliers.html", context=context)


def balance_suppliers_purchases_export(request):
    """View de l'étape 5.1 Fournisseurs M vs M-1"""
    """Export Excel de
    :param request: Request Django
    :return: response_file"""
    try:
        if request.method == "GET":
            today = pendulum.now()
            file_name = (
                "CONTROLE_FACTURES_FOURNISSEURS_"
                f"{today.format('Y_M_D')}{today.int_timestamp}.xlsx"
            )
            billing_period = (
                EdiValidation.objects.filter(
                    Q(final=False) | Q(final__isnull=True)).first().billing_period
            )

            return response_file(
                excel_balance_suppliers_purchases,
                file_name,
                CONTENT_TYPE_EXCEL,
                {"initial_date": billing_period},
            )

    except:
        LOGGER_VIEWS.exception("view : balance_suppliers_purchases_export")

    return redirect(reverse("validation_purchases:balance_suppliers_purchases"))


def balance_suppliers_purchases_validation(request):
    """Validation de l'écran 5.1 Fournisseurs M vs M-1"""

    if not request.is_ajax() and request.method != "POST":
        return redirect("home")

    level = 50
    request.session["level"] = 50
    message = "Il y a eu une erreur pendant la validation"
    data = {"success": "ko"}

    form = SuppliersValidationForm(request.POST or None)

    if form.is_valid():
        try:
            uuid_identification = form.cleaned_data.get("uuid_identification")
            suppliers_after = form.cleaned_data.get("suppliers", False)
            before_kwargs = {
                "uuid_identification": uuid_identification,
            }
            update_kwargs = {
                "uuid_identification": uuid_identification,
                "suppliers": suppliers_after,
            }
            trace_change(request, EdiValidation, before_kwargs, update_kwargs)

            if suppliers_after:
                request.session["level"] = 20
                message = "Le contrôle des fournisseurs est maintenant validé"
                data["success"] = "ok"
            else:
                request.session["level"] = 50
                message = "Le contrôle des fournisseurs est maintenant invalidé"

        except:
            LOGGER_VIEWS.exception(
                f"Views : balance_suppliers_purchases_validation error : {form.cleaned_data!r}"
            )

    else:
        LOGGER_VIEWS.exception(
            f"Views : balance_suppliers_purchases_validation error, form invalid : {form.errors!r}"
        )

    messages.add_message(request, level, message)

    return JsonResponse(data)
