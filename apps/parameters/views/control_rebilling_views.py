""" "
Views des Paramètres des Controles de Refacturation
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
from apps.core.functions.functions_http_response import (
    response_file,
    CONTENT_TYPE_EXCEL,
)
from apps.parameters.excel_outputs.parameters_excel_control_rebilling_list import (
    excel_liste_control_rebilling,
)
from apps.parameters.models import ControlRebilling
from apps.parameters.forms import (
    ControlRebillingForm,
    DeleteControlRebillingForm,
)

REVERSE_URL = "parameters:control_rebilling_list"


# ECRANS DES CONTROLES DE REFACTURATION ============================================================
class ControlRebillingList(ListView):
    """View de la liste des Contrôles de Refacturation"""

    model = ControlRebilling
    context_object_name = "controls"
    template_name = "parameters/control_rebilling_list.html"
    extra_context = {"titre_table": "Contrôles de Refacturation"}


class ControlRebillingCreate(ChangeTraceMixin, SuccessMessageMixin, CreateView):
    """CreateView de création des Contrôles de Refacturation"""

    model = ControlRebilling
    form_class = ControlRebillingForm
    form_class.use_required_attribute = False
    template_name = "parameters/control_rebilling_update.html"
    success_message = "Le Contrôle de Refacturation %(name)s a été créé avec success"
    error_message = (
        "Le Contrôle de Refacturation %(name)s n'a pu être créé, une erreur c'est produite"
    )

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["create"] = True
        context["chevron_retour"] = reverse(REVERSE_URL)
        context["titre_table"] = "Création Contrôle de Refacturation"
        return context

    def form_valid(self, form):
        """Ajout de l'user à la sauvegarde du formulaire"""
        form.instance.created_by = self.request.user
        self.request.session["level"] = 20

        return super().form_valid(form)


class ControlRebillingUpdate(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView pour modification des Contrôles de Refacturation"""

    model = ControlRebilling
    form_class = ControlRebillingForm
    form_class.use_required_attribute = False
    template_name = "parameters/control_rebilling_update.html"
    success_message = (
        "Le Contrôle de Refacturation  %(name)s a été modifiée avec success"
    )
    error_message = (
        "Le Contrôle de Refacturation  %(name)s n'a pu être modifiée, une erreur c'est produite"
    )

    def get_context_data(self, **kwargs):
        """Insert the form into the context dict."""

        context = super().get_context_data(**kwargs)
        context["titre_table"] = "Mise à jour Contrôle de Refacturation"
        context["chevron_retour"] = reverse(REVERSE_URL)
        return super().get_context_data(**context)

    def form_valid(self, form, **kwargs):
        """Ajout de l'user à la sauvegarde du formulaire"""
        form.instance.modified_by = self.request.user
        self.request.session["level"] = 20

        return super().form_valid(form)


@transaction.atomic
def delete_control_rebilling(request):
    """Suppression des Contrôles de Refacturation
    :param request: Request Django
    :return: view
    """

    if not request.is_ajax() and request.method != "POST":
        return redirect("home")

    data = {"success": "ko"}
    id_pk = request.POST.get("pk")
    form = DeleteControlRebillingForm({"id": id_pk})

    if form.is_valid():
        trace_mark_delete(
            request=request,
            django_model=ControlRebilling,
            data_dict={"id": id_pk},
            force_delete=True,
        )
        data = {"success": "success"}

    else:
        LOGGER_VIEWS.exception(
            f"delete_control_rebilling, form invalid : {form.errors!r}"
        )

    return JsonResponse(data)


def control_rebilling_export_list(_):
    """
    Export Excel de la liste des Sociétés
    :param _: Request Django
    :return: response_file
    """
    try:
        today = pendulum.now()
        file_name = (
            "LISTING_DES_CONTROLES_DE_REFACTURATION_"
            f"{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"
        )

        return response_file(
            excel_liste_control_rebilling, file_name, CONTENT_TYPE_EXCEL
        )

    except Exception as error:
        LOGGER_EXPORT_EXCEL.exception(f"view - control_rebilling_export_list : {error!r}")

    return redirect(reverse(REVERSE_URL))
