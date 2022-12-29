import pendulum
from django.db.models import Count
from django.shortcuts import render, reverse, redirect

from heron.loggers import LOGGER_VIEWS
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.edi.bin.cct_update import update_cct_edi_import
from apps.edi.models import EdiImport
from apps.validation_purchases.excel_outputs.excel_integration_invoices_without_cct import (
    excel_integration_without_cct,
)


# CONTROLES ETAPE 2.2 - FACTURES SANS CCT


def without_cct_purchases(request):
    """View de l'étape 2.2 des écrans de contrôles
    Visualisation des factures sans CCT
    :param request: Request Django
    :return: view
    """
    # on met à jour les cct au cas où l'on est rempli des cct dans un autre écran
    update_cct_edi_import()

    context = {
        "titre_table": "2.2 - Listing Factures sans CCT - Achats",
        "invoices_without_cct": EdiImport.objects.filter(cct_uuid_identification__isnull=True)
        .exclude(delete=True)
        .values(
            "third_party_num",
            "supplier",
            "code_maison",
            "maison",
            "invoice_number",
            "invoice_date",
            "invoice_amount_without_tax",
            "invoice_amount_with_tax",
        )
        .annotate(dcount=Count("third_party_num"))
        .order_by("third_party_num", "invoice_number"),
        "nature": "La facture n° ",
        "nb_paging": 100,
    }
    return render(
        request, "validation_purchases/without_cct_invoices_suppliers.html", context=context
    )


def without_cct_purchases_export(request):
    """Export Excel de
    :param request: Request Django
    :return: response_file"""

    try:
        if request.method == "GET":
            today = pendulum.now()
            file_name = (
                f"FACTURES_INTEGREES_SANS_CCT_{today.format('Y_M_D')}{today.int_timestamp}.xlsx"
            )

            return response_file(
                excel_integration_without_cct,
                file_name,
                CONTENT_TYPE_EXCEL,
            )

    except:
        LOGGER_VIEWS.exception("view : without_cct_purchases_export")

    return redirect(reverse("validation_purchases:without_cct_purchases"))
