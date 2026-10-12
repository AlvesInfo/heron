"""
Views des exclusions des rfa pour les clients / cct
"""

import pendulum
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView, CreateView, UpdateView

from apps.core.functions.functions_http import is_ajax
from heron.loggers import LOGGER_VIEWS, LOGGER_EXPORT_EXCEL
from apps.core.bin.change_traces import ChangeTraceMixin
from apps.core.bin.change_traces import trace_mark_delete
from apps.core.functions.functions_http_response import (
    response_file,
    CONTENT_TYPE_EXCEL,
)
from apps.rfa.models import ClientSupplierExclusion
from apps.rfa.excel_outputs.rfa_clients_suppliers_exclusion import (
    excel_list_rfa_clients_suppliers_exclusion,
)
from apps.rfa.forms import (
    ClientSupplierExclusionForm,
    DeleteClientSupplierExclusionForm,
)


# ECRANS DES CLIENTS ===============================================================================
class ClientSupplierExclusionList(ListView):
    """View de la liste des Exclusions RFA des Clients/Fournisseurs"""

    model = ClientSupplierExclusion
    context_object_name = "rfa_parameters"
    template_name = "rfa/clients_suppliers_exclusions_list.html"
    extra_context = {"titre_table": "CLIENTS/FOURNISSEURS A EXCLURE DU CALCUL DES RFA"}


class ClientSupplierExclusionCreate(ChangeTraceMixin, SuccessMessageMixin, CreateView):
    """CreateView des exclusions rfa des Clients/Fournisseurs"""

    model = ClientSupplierExclusion
    form_class = ClientSupplierExclusionForm
    template_name = "rfa/clients_suppliers_exclusions_update.html"
    success_message = "L'Exclusion du Client %(maison)s a été créé avec success"
    error_message = (
        "L'Exclusion du Client %(maison)s n'a pu être créé, une erreur c'est produite"
    )

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["create"] = True
        context["chevron_retour"] = reverse("rfa:clients_suppliers_exclusion_list")
        context["titre_table"] = "Création d'une nouvelle Exclusion Client pour les RFA"
        return context

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        return reverse("rfa:clients_suppliers_exclusion_list")

    def form_valid(self, form):
        """Ajout d'user à la sauvegarde du formulaire"""
        form.instance.created_by = self.request.user
        self.request.session["level"] = 20

        return super().form_valid(form)


class ClientSupplierExclusionUpdate(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView  des exclusions rfa des Clients/Fournisseurs"""

    model = ClientSupplierExclusion
    form_class = ClientSupplierExclusionForm
    template_name = "rfa/clients_suppliers_exclusions_update.html"
    success_message = "L'Exclusion du Client %(maison)s a été modifiée avec success"
    error_message = (
        "L'Exclusion du Client %(maison)s n'a pu être modifiée, une erreur c'est produite"
    )

    def get_context_data(self, **kwargs):
        """Insert the form into the context dict."""

        context = super().get_context_data(**kwargs)
        context["titre_table"] = "Mise à jour Exclusion Client"
        context["chevron_retour"] = reverse("rfa:clients_suppliers_exclusion_list")
        return super().get_context_data(**context)

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        return reverse("rfa:clients_suppliers_exclusion_list")

    def form_valid(self, form, **kwargs):
        """Ajout d'user à la sauvegarde du formulaire"""
        form.instance.modified_by = self.request.user
        self.request.session["level"] = 20

        return super().form_valid(form)


@transaction.atomic
def client_supplier_exclusion_delete(request):
    """Suppression des exclusions des Clients/Fournisseurs pour les RFA
    :param request: Request Django
    :return: view
    """

    if not is_ajax(request) or request.method != "POST":
        return redirect("home")

    data = {"success": "ko"}
    id_pk = request.POST.get("pk")
    form = DeleteClientSupplierExclusionForm({"id": id_pk})

    if form.is_valid():
        trace_mark_delete(
            request=request,
            django_model=ClientSupplierExclusion,
            data_dict={"id": id_pk},
            force_delete=True,
        )
        data = {"success": "success"}

    else:
        LOGGER_VIEWS.exception(
            f"client_supplier_exclusion_delete, form invalid : {form.errors!r}"
        )

    return JsonResponse(data)


def client_supplier_exclusion_export_list(_):
    """
    Export Excel de la liste des Exclusions RFA des Clients/Fournisseurs
    :param _: Request Django
    :return: response_file
    """
    try:
        today = pendulum.now()
        file_name = (
            "LISTING_DES_EXCLUSIONS_RFA_CLIENTS_CCT_"
            f"{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"
        )

        return response_file(
            excel_list_rfa_clients_suppliers_exclusion, file_name, CONTENT_TYPE_EXCEL
        )

    except Exception as error:
        LOGGER_EXPORT_EXCEL.exception(
            f"view : client_supplier_exclusion_export_list : {error!r}"
        )

    return redirect(reverse("rfa:clients_suppliers_exclusion_list"))
