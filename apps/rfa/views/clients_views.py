# pylint: disable=E0401,R0901,W0702,E1101,W0201,W1203
"""
Views des Paramètres
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
from apps.rfa.models import SignboardExclusion
from apps.rfa.excel_outputs.rfa_signboards_exclusion import excel_list_rfa_signboards_exclusion
from apps.rfa.forms import SignboardExclusionForm


# ECRANS DES Enseignes ============================================================================
class SignboardExclusionList(ListView):
    """View de la liste des Exclusions RFA des Enseignes"""

    model = SignboardExclusion
    context_object_name = "rfa_parameters"
    template_name = "rfa/rfa_parameters_list.html"
    extra_context = {"titre_table": "Enseignes"}


class SignboardExclusionCreate(ChangeTraceMixin, SuccessMessageMixin, CreateView):
    """CreateView de création des Enseignes"""

    model = SignboardExclusion
    form_class = SignboardExclusionForm
    form_class.use_required_attribute = False
    template_name = "rfa/rfa_parameter_update.html"
    success_message = "L'Exclusion de l'Enseigne %(name)s a été créé avec success"
    error_message = "L'Exclusion de l'Enseigne %(name)s n'a pu être créé, une erreur c'est produite"

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["create"] = True
        context["chevron_retour"] = reverse("rfa:signboards_exclusion_list")
        context["titre_table"] = "Création d'une nouvelle Exclusion Enseigne pour les RFA"
        return context

    def form_valid(self, form):
        """Ajout de l'user à la sauvegarde du formulaire"""
        form.instance.created_by = self.request.user
        self.request.session["level"] = 20

        return super().form_valid(form)


class SignboardExclusionUpdate(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView pour modification des identifiants pour les fournisseurs EDI"""

    model = SignboardExclusion
    form_class = SignboardExclusionForm
    form_class.use_required_attribute = False
    template_name = "rfa/rfa_parameter_update.html"
    success_message = "L'Exclusion de l'Enseigne %(name)s a été modifiée avec success"
    error_message = "L'Exclusion de l'Enseigne %(name)s n'a pu être modifiée, une erreur c'est produite"

    def get_context_data(self, **kwargs):
        """Insert the form into the context dict."""

        context = super().get_context_data(**kwargs)
        context["titre_table"] = "Mise à jour Exclusion Enseigne"
        context["chevron_retour"] = reverse("rfa:signboards_exclusion_list")
        return super().get_context_data(**context)

    def form_valid(self, form, **kwargs):
        """Ajout de l'user à L'sauvegarde du formulaire"""
        form.instance.modified_by = self.request.user
        self.request.session["level"] = 20

        return super().form_valid(form)


@transaction.atomic
def delete_sub_category(request):
    """Suppression des rubriques prestas
    :param request: Request Django
    :return: view
    """

    if not request.is_ajax() and request.method != "POST":
        return redirect("home")

    data = {"success": "ko"}
    id_pk = request.POST.get("pk")
    form = DeleteSubCategoryForm({"id": id_pk})

    if form.is_valid():
        trace_mark_delete(
            request=request,
            django_model=SubCategory,
            data_dict={"id": id_pk},
            force_delete=True,
        )
        data = {"success": "success"}

    else:
        LOGGER_VIEWS.exception(f"delete_invoice_purchase, form invalid : {form.errors!r}")

    return JsonResponse(data)


def signboard_exclusion_export_list(_):
    """
    Export Excel de la liste des Exclusions RFA des Enseignes
    :param _: Request Django
    :return: response_file
    """
    try:

        today = pendulum.now()
        file_name = f"LISTING_DES_EXCLUSIONS_RFA_ENSEIGNES_{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"

        return response_file(excel_list_rfa_signboards_exclusion, file_name, CONTENT_TYPE_EXCEL)

    except:
        LOGGER_EXPORT_EXCEL.exception("view : signboard_exclusion_export_list")

    return redirect(reverse("rfa:signboards_exclusion_list"))

