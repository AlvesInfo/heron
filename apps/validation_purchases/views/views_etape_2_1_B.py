from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse
from django.shortcuts import render, redirect, reverse
from django.views.generic import UpdateView

from heron.loggers import LOGGER_VIEWS
from apps.core.bin.change_traces import ChangeTraceMixin, trace_mark_delete
from apps.core.bin.encoders import get_base_64, set_base_64_list
from apps.edi.models import EdiImport
from apps.validation_purchases.forms import (
    EdiImportValidationForm,
    UpdateSupplierPurchasesForm,
    DeletePkForm,
)


# CONTROLES ETAPE 2.1.B - DETAILS FACTURES


def details_purchase(request, enc_param):
    """View de l'étape 2.B des écrans de contrôles
    Visualisation des détails des lignes d'une facture pour un fournisseur
    :param request: Request Django
    :param enc_param: paramètres encodés en base 64
    :return: view
    """
    big_category, third_party_num, supplier, invoice_month, invoice_number = get_base_64(enc_param)

    context = {
        "titre_table": f"Contrôle : {supplier} - INVOICE N° {invoice_number}",
        "invoices": EdiImport.objects.filter(
            big_category__name=big_category,
            third_party_num=third_party_num,
            supplier=supplier,
            invoice_month=invoice_month,
            invoice_number=invoice_number,
        ).order_by("pk"),
        "chevron_retour": reverse(
            "validation_purchases:integration_supplier_purchases",
            kwargs={
                "enc_param": set_base_64_list(
                    [big_category, third_party_num, supplier, invoice_month]
                ),
            },
        ),
        "nature": "La ligne n° ",
        "nb_paging": 50,
    }

    return render(request, "validation_purchases/details_invoices_suppliers.html", context=context)


def delete_line_details_purchase(request):
    """Suppression des lignes de factures non souhaitées
    :param request: Request Django
    :return: view
    """

    if not request.is_ajax() and request.method != "POST":
        return redirect("home")

    data = {"success": "ko"}
    data_dict = {
        "pk": request.POST.get("pk[pk]"),
    }
    form = DeletePkForm(data_dict)

    if form.is_valid() and form.cleaned_data:
        trace_mark_delete(
            request=request,
            django_model=EdiImport,
            data_dict=form.cleaned_data,
            force_delete=True,
        )
        data = {"success": "success"}

    else:
        LOGGER_VIEWS.exception(f"delete_line_details_purchase, form invalid : {form.errors!r}")

    return JsonResponse(data)


def details_purchases_export(request):
    """Export Excel de
    :param request: Request Django
    :return: response_file
    """
    context = {"titre_table": "Export Excel"}
    return render(request, "validation_purchases/details_invoices_suppliers.html", context=context)


class UpdateDetaisPurchase(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView pour modification des factures founisseurs"""

    model = EdiImport
    form_class = EdiImportValidationForm
    form_class.use_required_attribute = False
    template_name = "book/society_update.html"
    success_message = "La facture N° %(invoice_number)s a été modifiée avec success"
    error_message = (
        "La facture N° %(invoice_number)s n'a pu être modifiée, une erreur c'est produite"
    )
