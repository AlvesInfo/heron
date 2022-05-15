# pylint: disable=R0903
"""
Views
"""
import os
from pathlib import Path
import hashlib
from datetime import timedelta, date

import pendulum
from django.http import JsonResponse
from django.shortcuts import redirect, reverse
from django.views.generic.edit import FormView
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView, UpdateView, CreateView
from django.views.decorators.csrf import csrf_protect
from django.db.models import Q

from heron import settings
from heron.loggers import ERROR_VIEWS_LOGGER
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.book.excel_outputs.book_excel_societies_list import excel_liste_societies
from apps.book.models import Society


# ECRANS DES FOURNISSEURS ==========================================================================
class SuppliersList(ListView):
    """View de la liste des Tiers X3"""
    model = Society
    context_object_name = "societies"
    template_name = "book/societies_list.html"


class UpdateBanque(UpdateView):
    model = Society
    fields = [
        "third_party_num",
        "name",
        "siret_number",
        "vat_cee_number",
        "invoice_supplier_name",
        "invoice_supplier_identifiaction",
    ]
    template_name = "book/society_view.html"
    success_message = "Le Tiers %(third_party_num)s a été modifiée avec success"
    error_message = "La Tiers %(third_party_num)s n'a pu être modifiée, une erreur c'est produite"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["chevron_retour"] = reverse("book:societies_list")
        return context

    def form_valid(self, form):
        form.instance.modified_by = self.request.user
        self.request.session["level"] = 20
        return super().form_valid(form)

    def form_invalid(self, form):
        self.request.session["level"] = 50
        return super().form_invalid(form)


def export_list_societies(request):
    """
    Export Excel de la liste des Sociétés
    :param request: Request Django
    :return: response_file
    """
    if request.method == "POST":
        try:

            today = pendulum.now()
            if "export_list_societies" in request.POST:
                societies = Society.objects.all()
                society_type = "tiers"
                file_name = f"LISTING_DES_TIERS_{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"

            elif "export_list_clients" in request.POST:
                societies = Society.objects.filter(is_client=True)
                society_type = "clients"
                file_name = (
                    f"LISTING_DES_CLIENTS_{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"
                )

            elif "export_list_supplierss" in request.POST:
                societies = Society.objects.filter(is_supplier=True)
                society_type = "suppliers"
                file_name = (
                    f"LISTING_DES_FOURNISSEURS_{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"
                )

            else:
                return redirect(reverse("book:societies_list"))

            return response_file(
                excel_liste_societies, file_name, CONTENT_TYPE_EXCEL, societies, society_type
            )

        except:
            ERROR_VIEWS_LOGGER.exception("view : export_list_societies")

    return redirect(reverse("book:societies_list"))
