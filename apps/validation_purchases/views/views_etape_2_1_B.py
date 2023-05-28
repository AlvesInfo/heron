# pylint: disable=E0401,C0103,W1203,W0702
"""
Views des details d'une facture
"""
import pendulum
from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse
from django.shortcuts import render, redirect, reverse
from django.views.generic import UpdateView
from django.db.models import Value
from django.contrib.postgres.aggregates import StringAgg

from heron.loggers import LOGGER_VIEWS
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.core.bin.change_traces import ChangeTraceMixin, trace_mark_delete
from apps.core.bin.encoders import get_base_64, set_base_64_list
from apps.edi.models import EdiImport
from apps.validation_purchases.forms import (
    EdiImportValidationForm,
    ChangeBigCategoryForm,
    DeletePkForm,
    ChangeCttForm,
)
from apps.validation_purchases.excel_outputs.excel_supplier_invoices_number import (
    excel_invoice_number,
)


# CONTROLES ETAPE 2.1.B - DETAILS FACTURES


def details_purchase(request, enc_param):
    """View de l'étape 2.B des écrans de contrôles
    Visualisation des détails des lignes d'une facture pour un fournisseur
    :param request: Request Django
    :param enc_param: paramètres encodés en base 64
    :return: view
    """
    third_party_num, supplier, invoice_month, invoice_number = get_base_64(enc_param)
    invoices = (
        EdiImport.objects.annotate(
            delivery_numbers=StringAgg(
                "delivery_number",
                delimiter=", ",
                distinct=True,
                default=Value(""),
                ordering="delivery_number",
            )
        )
        .filter(
            third_party_num=third_party_num,
            supplier=supplier,
            invoice_month=invoice_month,
            invoice_number=invoice_number,
        )
        .order_by("pk")
    )

    context = {
        "titre_table": f"Contrôle : {supplier} - INVOICE N° {invoice_number}",
        "invoices": invoices,
        "chevron_retour": reverse(
            "validation_purchases:integration_supplier_purchases",
            kwargs={
                "enc_param": set_base_64_list([third_party_num, supplier, invoice_month]),
            },
        ),
        "form": ChangeBigCategoryForm(),
        "cct_form": ChangeCttForm(),
        "nb_paging": 50,
        "enc_param": enc_param,
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


def details_purchases_export(request, enc_param):
    """Export Excel de
    :param request: Request Django
    :param enc_param: Paramètres get de la requête encodée base 64
    :return: response_file
    """
    try:
        if request.method == "GET":
            third_party_num, supplier, invoice_month, invoice_number = get_base_64(enc_param)
            today = pendulum.now()
            file_name = (
                f"{third_party_num}_{invoice_number}_"
                f"{today.format('Y_M_D')}{today.int_timestamp}.xlsx"
            )
            attr_dict = {
                "third_party_num": third_party_num,
                "supplier": supplier,
                "invoice_month": invoice_month,
                "invoice_number": invoice_number,
            }
            return response_file(
                excel_invoice_number,
                file_name,
                CONTENT_TYPE_EXCEL,
                attr_dict,
            )

    except:
        LOGGER_VIEWS.exception("view : details_purchases_export")

    return redirect(
        reverse("validation_purchases:details_purchase", kwargs={"enc_param": enc_param})
    )


class UpdateDetailsPurchase(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView pour modification des factures founisseurs"""

    model = EdiImport
    form_class = EdiImportValidationForm
    form_class.use_required_attribute = False
    template_name = "book/society_update.html"
    success_message = "La facture N° %(invoice_number)s a été modifiée avec success"
    error_message = (
        "La facture N° %(invoice_number)s n'a pu être modifiée, une erreur c'est produite"
    )

    def form_valid(self, form):
        """Ajout de l'user à la sauvegarde du formulaire"""
        form.instance.modified_by = self.request.user
        self.request.session["level"] = 20

        return super().form_valid(form)
