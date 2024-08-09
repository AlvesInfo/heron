# pylint: disable=E0401,R0901,W0702,E1101,W0201,W1203
"""
Views des taux de RFA par founisseurs
"""
import pendulum
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, reverse
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView, CreateView, UpdateView

from heron.loggers import LOGGER_VIEWS, LOGGER_EXPORT_EXCEL
from apps.core.bin.change_traces import ChangeTraceMixin
from apps.core.bin.change_traces import trace_mark_delete
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.rfa.models import SupplierRate
from apps.rfa.excel_outputs.rfa_suppliers_rate import excel_list_suppliers_rate
from apps.rfa.forms import SupplierRateForm, DeleteSupplierRateForm


# ECRANS DES TAUX RFA ==============================================================================
class SupplierRateList(ListView):
    """View de la liste des Taux de RFA Fournisseurs"""

    model = SupplierRate
    context_object_name = "rfa_parameters"
    template_name = "rfa/suppliers_rate_list.html"
    extra_context = {"titre_table": "Taux de RFA Fournisseurs"}


class SupplierRateCreate(ChangeTraceMixin, SuccessMessageMixin, CreateView):
    """CreateView des Taux de RFA Fournisseurs"""

    model = SupplierRate
    form_class = SupplierRateForm
    form_class.use_required_attribute = False
    template_name = "rfa/suppliers_rate_update.html"
    success_message = "Le taux de rfa pour le fournisseur %(supplier)s a été créé avec success"
    error_message = (
        "Le taux de RFA pour le fournisseur %(supplier)s "
        "n'a pu être créé, une erreur c'est produite"
    )

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["create"] = True
        context["chevron_retour"] = reverse("rfa:suppliers_rate_list")
        context["titre_table"] = "Création taux de RFA par fournisseur pour le calcul de RFA"
        return context

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        return reverse("rfa:suppliers_rate_list")

    def form_valid(self, form):
        """Ajout d'user à la sauvegarde du formulaire"""
        form.instance.created_by = self.request.user
        self.request.session["level"] = 20

        return super().form_valid(form)

    def form_invalid(self, form):
        """On surcharge la méthode form_invalid, pour ajouter le niveau de message et sa couleur."""
        # Si la view appelante souhaite faire quelque chose après une erreur dans le formulaire
        # On lance sa methode form_error
        if hasattr(self, "form_error"):
            form_error = getattr(self, "form_error")
            form_error()

        return super().form_invalid(form)


class SupplierRateUpdate(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView des Taux de RFA Fournisseurs"""

    model = SupplierRate
    form_class = SupplierRateForm
    form_class.use_required_attribute = False
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

    def form_valid(self, form, **kwargs):
        """Ajout d'user à la sauvegarde du formulaire"""
        form.instance.modified_by = self.request.user
        self.request.session["level"] = 20

        return super().form_valid(form)

    def form_invalid(self, form):
        """On surcharge la méthode form_invalid, pour ajouter le niveau de message et sa couleur."""
        # Si la view appelante souhaite faire quelque chose après une erreur dans le formulaire
        # On lance sa methode form_error
        if hasattr(self, "form_error"):
            form_error = getattr(self, "form_error")
            form_error()

        return super().form_invalid(form)


@transaction.atomic
def supplier_rate_delete(request):
    """Suppression des taux de RFA par fournisseur pour le calcul de RFA
    :param request: Request Django
    :return: view
    """

    if not request.is_ajax() and request.method != "POST":
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
        LOGGER_VIEWS.exception(f"supplier_rate_delete, form invalid : {form.errors!r}")

    return JsonResponse(data)


def supplier_rate_export_list(_):
    """
    Export Excel de la liste des taux de RFA par fournisseur pour le calcul de RFA
    :param _: Request Django
    :return: response_file
    """
    try:

        today = pendulum.now()
        file_name = (
            "LISTING_DES_TAUX_RFA_FOURNISSEURS_"
            f"{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"
        )

        return response_file(excel_list_suppliers_rate, file_name, CONTENT_TYPE_EXCEL)

    except:
        LOGGER_EXPORT_EXCEL.exception("view : supplier_rate_export_list")

    return redirect(reverse("rfa:suppliers_rate_list"))
