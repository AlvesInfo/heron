# pylint: disable=E0401,R0903
"""
Views des Maisons
"""

import pendulum
from django.shortcuts import redirect, reverse
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView, CreateView, UpdateView

from heron.loggers import ERROR_VIEWS_LOGGER
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.centers_clients.excel_outputs.centers_clients_excel_maisons_list import (
    excel_liste_maisons,
)
from apps.centers_clients.models import Maison
from apps.centers_clients.forms import MaisonForm


# ECRANS DES MAISONS ===============================================================================
class MaisonsList(ListView):
    """View de la liste des Maisons"""

    model = Maison
    context_object_name = "maisons"
    template_name = "centers_clients/maisons_list.html"
    extra_context = {"titre_table": "Maisons"}


class CreateMaison(SuccessMessageMixin, CreateView):
    """CreateView de création des Maisons"""

    model = Maison
    form_class = MaisonForm
    form_class.use_required_attribute = False
    template_name = "centers_clients/maisons_update.html"
    success_message = "La Maison %(cct)s a été créé avec success"
    error_message = "La Maison %(cct)s n'a pu être créé, une erreur c'est produite"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["create"] = True
        context["chevron_retour"] = reverse("centers_clients:maisons_list")
        context["titre_table"] = "Création d'une Maison"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.modified_by = self.request.user
        self.request.session["level"] = 20
        return super().form_valid(form)

    def form_invalid(self, form):
        self.request.session["level"] = 50
        return super().form_invalid(form)


class UpdateMaison(SuccessMessageMixin, UpdateView):
    """UpdateView pour modification des identifiants pour les fournisseurs EDI"""

    model = Maison
    form_class = MaisonForm
    form_class.use_required_attribute = False
    template_name = "centers_clients/maisons_update.html"
    success_message = "La Maison %(cct)s a été modifiée avec success"
    error_message = "La Maison %(cct)s n'a pu être modifiée, une erreur c'est produite"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["chevron_retour"] = reverse("centers_clients:maisons_list")
        context["titre_table"] = (
            f"Mise à jour de la Maison : "
            f"{context.get('object').cct} - "
            f"{context.get('object').intitule}"
        )
        return context

    def form_valid(self, form):
        form.instance.modified_by = self.request.user
        self.request.session["level"] = 20
        return super().form_valid(form)

    def form_invalid(self, form):
        self.request.session["level"] = 50
        return super().form_invalid(form)


def export_list_maisons(request):
    """
    Export Excel de la liste des Sociétés
    :param request: Request Django
    :return: response_file
    """
    if request.method == "POST":
        try:

            today = pendulum.now()

            if "export_list_maisons" in request.POST:
                file_name = (
                    f"LISTING_DES_MAISONS_{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"
                )

            else:
                return redirect(reverse("centers_clients:maisons_list"))

            return response_file(excel_liste_maisons, file_name, CONTENT_TYPE_EXCEL)

        except:
            ERROR_VIEWS_LOGGER.exception("view : export_list_maisons")

    return redirect(reverse("centers_clients:maisons_list"))
