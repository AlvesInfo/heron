import pendulum
from django.db import connection, transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect, reverse

from heron.loggers import LOGGER_VIEWS
from apps.core.bin.change_traces import trace_mark_delete
from apps.core.bin.encoders import get_base_64
from apps.core.functions.functions_postgresql import query_file_dict_cursor
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.validation_purchases.excel_outputs import excel_supplier_purchases, excel_transfers_cosium
from apps.edi.models import EdiImport
from apps.validation_purchases.forms import (
    DeleteInvoiceForm,
)
from apps.validation_purchases.forms import ChangeCttForm


# CONTROLES ETAPE 2.1.A - LISTING FACTURES


def integration_supplier_purchases(request, enc_param):
    """View de l'étape 2.A des écrans de contrôles
    Visualisation des montants par Factures pour le fournisseur demandé
    :param request: Request Django
    :param enc_param: paramètres encodés en base 64
    :return: view
    """
    sql_context_file = "apps/validation_purchases/sql_files/sql_integration_supplier_purchases.sql"
    third_party_num, supplier, invoice_month, flow_name = get_base_64(enc_param)

    with connection.cursor() as cursor:
        elements = query_file_dict_cursor(
            cursor,
            file_path=sql_context_file,
            parmas_dict={
                "third_party_num": third_party_num,
                "supplier": supplier,
                "invoice_month": invoice_month,
                "flow_name": flow_name,
            },
        )

        if not elements:
            return redirect(reverse("validation_purchases:integration_purchases"))

        mois = pendulum.parse(invoice_month).format("MMMM YYYY", locale="fr").capitalize()

        context = {
            "titre_table": f"Contrôle ({flow_name}) : {third_party_num}  - {supplier}  - {mois}",
            "controles_exports": elements,
            "chevron_retour": reverse("validation_purchases:integration_purchases"),
            "nature": "La facture n° ",
            "nb_paging": 25,
            "cct_form": ChangeCttForm(),
            "enc_param": enc_param,
            "flow_name": flow_name,
        }

    return render(request, "validation_purchases/listing_invoices_suppliers.html", context=context)


@transaction.atomic
def delete_invoice_purchase(request):
    """Suppression des factures non souhaitées
    :param request: Request Django
    :return: view
    """

    if not request.is_ajax() and request.method != "POST":
        return redirect("home")

    data = {"success": "ko"}
    third_party_num, invoice_number, invoice_month, _ = request.POST.values()
    data_dict = {
        "third_party_num": third_party_num,
        "invoice_number": invoice_number,
        "invoice_month": invoice_month,
    }
    form = DeleteInvoiceForm(data_dict)

    if form.is_valid() and form.cleaned_data:
        trace_mark_delete(
            request=request,
            django_model=EdiImport,
            data_dict=form.cleaned_data,
            force_delete=True,
        )
        data = {"success": "success"}

    else:
        LOGGER_VIEWS.exception(f"delete_invoice_purchase, form invalid : {form.errors!r}")

    return JsonResponse(data)


def integration_supplier_purchases_export(request, enc_param):
    """Export Excel de la liste des montants par Factures pour le fournisseur demandé
    :param request: Request Django
    :param enc_param: paramètres au format base64
    :return: response_file
    """
    try:
        if request.method == "GET":
            third_party_num, supplier, invoice_month, *_ = get_base_64(enc_param)
            today = pendulum.now()
            file_name = (
                f"{third_party_num}_{invoice_month}_"
                f"{today.format('Y_M_D')}{today.int_timestamp}.xlsx"
            )
            attr_dict = {
                "third_party_num": third_party_num,
                "supplier": supplier,
                "invoice_month": invoice_month,
            }
            return response_file(
                excel_transfers_cosium
                if supplier == "COSIUM TRANSFERTS"
                else excel_supplier_purchases,
                file_name,
                CONTENT_TYPE_EXCEL,
                attr_dict,
            )

    except:
        LOGGER_VIEWS.exception("view : integration_supplier_purchases_export")

    return redirect(reverse("validation_purchases:integration_purchases"))
