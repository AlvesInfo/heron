"""Views des taux de RFA par founisseurs."""

import pendulum
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import CreateView, ListView, UpdateView

from apps.core.bin.change_traces import ChangeTraceMixin, trace_mark_delete
from apps.core.functions.functions_http import is_ajax
from apps.core.functions.functions_http_response import CONTENT_TYPE_EXCEL, response_file
from apps.rfa.excel_outputs.rfa_suppliers_rate import excel_list_suppliers_rate
from apps.rfa.forms import DeleteSupplierRateForm, SupplierRateForm
from apps.rfa.models import SupplierRate
from heron.loggers import LOGGER_EXPORT_EXCEL, LOGGER_VIEWS


# ECRANS DES TAUX RFA ==============================================================================
class SupplierRateList(ListView):
    """View de la liste des Taux de RFA Fournisseurs."""

    model = SupplierRate
    context_object_name = "rfa_parameters"
    template_name = "rfa/suppliers_rate_list.html"
    extra_context = {"titre_table": "Taux de RFA Fournisseurs"}


class SupplierRateCreate(ChangeTraceMixin, SuccessMessageMixin, CreateView):
    """CreateView des Taux de RFA Fournisseurs."""

    model = SupplierRate
    form_class = SupplierRateForm
    template_name = "rfa/suppliers_rate_update.html"
    success_message = "Le taux de rfa pour le fournisseur %(supplier)s a été créé avec success"
    error_message = (
        "Le taux de RFA pour le fournisseur %(supplier)s "
        "n'a pu être créé, une erreur c'est produite"
    )

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template."""
        context = super().get_context_data(**kwargs)
        context["create"] = True
        context["chevron_retour"] = reverse("rfa:suppliers_rate_list")
        context["titre_table"] = "Création taux de RFA par fournisseur pour le calcul de RFA"
        return context

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        return reverse("rfa:suppliers_rate_list")

    def form_valid(self, form):
        """Ajout d'user à la sauvegarde du formulaire."""
        form.instance.created_by = self.request.user
        self.request.session["level"] = 20

        return super().form_valid(form)


class SupplierRateUpdate(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView des Taux de RFA Fournisseurs."""

    model = SupplierRate
    form_class = SupplierRateForm
    template_name = "rfa/suppliers_rate_update.html"
    success_message = "Le taux de rfa pour le fournisseur %(supplier)s a été modifiée avec success"
    error_message = (
        "Le taux de rfa pour le fournisseur %(supplier)s "
        "n'a pu être modifiée, une erreur c'est produite"
    )

    def get_context_data(self, **kwargs):
        """Insert the form into the context dict."""
        context = super().get_context_data(**kwargs)
        context["titre_table"] = "Mise à jour taux de RFA par fournisseur pour le calcul de RFA"
        context["chevron_retour"] = reverse("rfa:suppliers_rate_list")
        return super().get_context_data(**context)

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        return reverse("rfa:suppliers_rate_list")

    def form_valid(self, form):
        """Ajout d'user à la sauvegarde du formulaire."""
        form.instance.modified_by = self.request.user
        self.request.session["level"] = 20

        return super().form_valid(form)


@transaction.atomic
def supplier_rate_delete(request):
    """Suppression des taux de RFA par fournisseur pour le calcul de RFA.

    :param request: Request Django
    :return: view.
    """
    if not is_ajax(request) or request.method != "POST":
        return redirect("home")

    data = {"success": "ko"}
    id_pk = request.POST.get("pk")
    form = DeleteSupplierRateForm({"id": id_pk})

    if form.is_valid():
        trace_mark_delete(
            request=request,
            django_model=SupplierRate,
            data_dict={"id": id_pk},
            force_delete=True,
        )
        data = {"success": "success"}

    else:
        LOGGER_VIEWS.error("supplier_rate_delete, form invalid : %r", form.errors)

    return JsonResponse(data)


def supplier_rate_export_list(_):
    """Export Excel de la liste des taux de RFA par fournisseur pour le calcul de RFA.

    :param _: Request Django
    :return: response_file.
    """
    try:
        today = pendulum.now()
        file_name = (
            f"LISTING_DES_TAUX_RFA_FOURNISSEURS_{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"
        )

        return response_file(excel_list_suppliers_rate, file_name, CONTENT_TYPE_EXCEL)

    except Exception:
        LOGGER_EXPORT_EXCEL.exception("view : supplier_rate_export_list")

    return redirect(reverse("rfa:suppliers_rate_list"))
