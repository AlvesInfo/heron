import pendulum
from django.db.models import Sum
from django.shortcuts import render, redirect, reverse

from heron.loggers import LOGGER_VIEWS
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.edi.models import EdiImport
from apps.validation_purchases.excel_outputs.excel_integration_invoices_familly import (
    excel_integration_invoices_familly,
)

# CONTROLES ETAPE 3.1 - CONTROLE FAMILLES


def families_invoices_purchases(request):
    """View de l'étape 3.1 des écrans de contrôles"""
    # TODO Changer la requête
    context = {
        "titre_table": "Contrôle des familles - Achats",
        "invoices_without_cct": EdiImport.objects.all()
        .exclude(delete=False)
        .values("third_party_num", "supplier", "axe_pro")
        .annotate(total_without_tax=Sum("net_amount"))
        .order_by("supplier"),
        "nature": "La facture n° ",
        "nb_paging": 100,
    }
    return render(request, "validation_purchases/families_invoices_suppliers.html", context=context)


def families_invoices_purchases_export(request):
    """Export Excel de
    :param request: Request Django
    :return: response_file"""
    try:
        if request.method == "GET":
            today = pendulum.now()
            file_name = (
                "FACTURES_CONTROLE_FAMILLES_"
                f"{today.format('Y_M_D')}{today.int_timestamp}.xlsx"
            )

            return response_file(
                excel_integration_invoices_familly,
                file_name,
                CONTENT_TYPE_EXCEL,
            )

    except:
        LOGGER_VIEWS.exception("view : integration_purchases_export")

    return redirect(reverse("validation_purchases:families_invoices_purchases"))
