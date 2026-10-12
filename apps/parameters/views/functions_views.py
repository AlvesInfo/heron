"""Views des Paramètres."""

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
from apps.parameters.excel_outputs.parameters_excel_functions import excel_liste_functions
from apps.parameters.forms import InvoiceFunctionsForm
from apps.parameters.models import InvoiceFunctions
from heron.loggers import LOGGER_EXPORT_EXCEL, LOGGER_VIEWS


# ECRANS DES FUNCTIONS =============================================================================
class FunctionsList(ListView):
    """View de la liste des Fonctions."""

    model = InvoiceFunctions
    context_object_name = "functions"
    template_name = "parameters/functions_list.html"
    extra_context = {"titre_table": "Fonctions"}


class FunctionCreate(ChangeTraceMixin, SuccessMessageMixin, CreateView):
    """CreateView de création des Fonctions."""

    model = InvoiceFunctions
    form_class = InvoiceFunctionsForm
    template_name = "parameters/function_update.html"
    success_message = "La Fonction %(function_name)s a été créé avec success"
    error_message = "La Fonction %(function_name)s n'a pu être créé, une erreur c'est produite"

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template."""
        context = super().get_context_data(**kwargs)
        context["create"] = True
        context["chevron_retour"] = reverse("parameters:functions_list")
        context["titre_table"] = "Création d'une nouvelle Fonction"

        return context

    def form_valid(self, form):
        """Ajout de l'user à la sauvegarde du formulaire."""
        form.instance.created_by = self.request.user
        self.request.session["level"] = 20

        return super().form_valid(form)


class FunctionUpdate(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView pour modification des Fonctions."""

    model = InvoiceFunctions
    form_class = InvoiceFunctionsForm
    template_name = "parameters/function_update.html"
    success_message = "La Fonction %(function_name)s a été modifiée avec success"
    error_message = "La Fonction %(function_name)s n'a pu être modifiée, une erreur c'est produite"

    def get_context_data(self, **kwargs):
        """Insert the form into the context dict."""
        context = super().get_context_data(**kwargs)
        context["titre_table"] = "Mise à jour Fonction"
        context["chevron_retour"] = reverse("parameters:functions_list")

        return super().get_context_data(**context)

    def form_valid(self, form):
        """Ajout de l'user à la sauvegarde du formulaire."""
        form.instance.modified_by = self.request.user
        self.request.session["level"] = 20

        return super().form_valid(form)


def functions_export_list(_):
    """Export Excel de la liste des Fonctions.

    :param _: Request Django
    :return: response_file.
    """
    try:
        today = pendulum.now()
        file_name = f"LISTING_DES_FONCTIONS_{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"

        return response_file(excel_liste_functions, file_name, CONTENT_TYPE_EXCEL)

    except Exception:
        LOGGER_EXPORT_EXCEL.exception("view : functions_export_list")

    return redirect(reverse("parameters:functions_list"))


@transaction.atomic
def function_delete(request):
    """Suppression des fonctions.

    :param request: Request Django
    :return: view.
    """
    if not is_ajax(request) or request.method != "POST":
        return redirect("home")

    try:
        invoice = InvoiceFunctions.objects.get(pk=request.POST.get("pk"))
        trace_mark_delete(
            request=request,
            django_model=InvoiceFunctions,
            data_dict={"id": invoice.pk},
            force_delete=True,
        )
        data = {"success": "success"}

    except (InvoiceFunctions.DoesNotExist, Exception):
        data = {"success": "ko"}
        LOGGER_VIEWS.exception(
            "views - function_delete, l'user : %r a tenter de supprimer une Fonction inexistante",
            request.user.email,
        )

    return JsonResponse(data)
