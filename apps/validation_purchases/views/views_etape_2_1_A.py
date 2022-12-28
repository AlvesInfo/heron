import pendulum
from django.contrib.messages.views import SuccessMessageMixin
from django.db import connection, transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect, reverse
from django.views.generic import UpdateView

from heron.loggers import LOGGER_VIEWS
from apps.core.bin.change_traces import ChangeTraceMixin, trace_mark_delete
from apps.core.bin.encoders import get_base_64
from apps.core.functions.functions_postgresql import query_file_dict_cursor
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.validation_purchases.excel_outputs import (
    excel_supplier_purchases,
)

from apps.edi.models import EdiImport
from apps.edi.forms import (
    DeleteInvoiceForm,
)
from apps.edi.models import EdiImportControl
from apps.edi.forms import EdiImportControlForm


# CONTROLES ETAPE 2.1.A - LISTING FACTURES


def integration_supplier_purchases(request, enc_param):
    """View de l'étape 2.A des écrans de contrôles
    Visualisation des montants par Factures pour le fournisseur demandé
    :param request: Request Django
    :param enc_param: paramètres encodés en base 64
    :return: view
    """
    sql_context_file = "apps/validation_purchases/sql_files/sql_integration_supplier_purchases.sql"
    big_category, third_party_num, supplier, invoice_month = get_base_64(enc_param)

    with connection.cursor() as cursor:
        elements = query_file_dict_cursor(
            cursor,
            file_path=sql_context_file,
            parmas_dict={
                "third_party_num": third_party_num,
                "supplier": supplier,
                "big_category": big_category,
                "invoice_month": invoice_month,
            },
        )

        if elements:
            titre_table = elements[0]
            mois = (
                pendulum.parse(titre_table.get("invoice_month").isoformat())
                .format("MMMM YYYY", locale="fr")
                .capitalize()
            )

        else:
            mois = ""

        context = {
            "titre_table": f"Contrôle : {supplier}  - {mois}",
            "controles_exports": elements,
            "chevron_retour": reverse("validation_purchases:integration_purchases"),
            "nature": "La facture n° ",
            "nb_paging": 100,
        }

    return render(request, "validation_purchases/listing_invoices_suppliers.html", context=context)


class UpdateSupplierPurchases(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView pour modification des factures founisseurs"""

    model = EdiImportControl
    form_class = EdiImportControlForm
    form_class.use_required_attribute = False
    template_name = "book/society_update.html"
    success_message = (
        "La saisie de contrôle pour le tiers %(third_party_num)s "
        "du mois : %(invoice_month)s, a été modifiée avec success"
    )
    error_message = (
        "La saisie de contrôle pour le tiers N° %(third_party_num)s "
        "n'a pu être modifiée, une erreur c'est produite"
    )


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
            big_category, third_party_num, supplier, invoice_month, _ = get_base_64(enc_param)
            today = pendulum.now()
            file_name = (
                f"{big_category}_{third_party_num}_{invoice_month}_"
                f"{today.format('Y_M_D')}{today.int_timestamp}.xlsx"
            )
            attr_dict = {
                "big_category": big_category,
                "third_party_num": third_party_num,
                "supplier": supplier,
                "invoice_month": invoice_month,
            }
            return response_file(
                excel_supplier_purchases,
                file_name,
                CONTENT_TYPE_EXCEL,
                attr_dict,
            )

    except:
        LOGGER_VIEWS.exception("view : integration_supplier_purchases_export")

    return redirect(reverse("validation_purchases:integration_purchases"))
