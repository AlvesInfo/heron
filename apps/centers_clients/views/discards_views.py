# pylint: disable=E0401,R0903,W0201,W0702,W0613,W1203
"""
Views des Maisons à écarter par founisseurs

Commentaire:

created at: 2023-01-20
created by: Paulo ALVES

modified at: 2023-01-20
modified by: Paulo ALVES
"""
from pathlib import Path

import pendulum
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.core.files import File
from django.views.generic import ListView, CreateView, UpdateView

from heron.loggers import LOGGER_VIEWS
from heron.settings import PICKLERS_DIR
from apps.core.bin.change_traces import ChangeTraceMixin
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.core.models import PicklerFiles
from apps.centers_clients.excel_outputs.centers_clients_excel_maisons_list import (
    excel_liste_maisons,
)
from apps.accountancy.models import CctSage
from apps.book.models import Society
from apps.centers_clients.models import MaisonSupllierExclusion
from apps.centers_clients.forms import MaisonSupllierExclusionForm


class MaisonSupllierExclusionList(ListView):
    """View de la liste des Tiers X3"""

    model = MaisonSupllierExclusion
    context_object_name = "exclusions"
    template_name = "centers_clients/exclusions_list.html"
    extra_context = {"titre_table": "Couples d'exclusion Tiers X3/Client"}


class MaisonSupllierExclusionCreate(ChangeTraceMixin, SuccessMessageMixin, CreateView):
    """CreateView de création des couples Tiers / Masions à exlucre de la facturation"""

    model = MaisonSupllierExclusion
    form_class = MaisonSupllierExclusionForm
    form_class.use_required_attribute = False
    template_name = "centers_clients/exclusion_update.html"
    success_message = (
        "Le couple d'exclusion, %(third_party_num)s - %(maison)s a été créé avec success"
    )
    error_message = (
        "Le couple d'exclusion, %(third_party_num)s - %(maison)s n'a pu être créé, "
        "une erreur c'est produite"
    )

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["chevron_retour"] = reverse("centers_clients:exclusions_list")
        context["titre_table"] = "Création d'un nouveau couple d'exclusion Tiers X3/Client"
        return context

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        return reverse("home")

    def form_valid(self, form):
        """
        On surcharge la méthode form_valid, pour supprimer les fichiers picklers au success du form.
        """
        form.instance.modified_by = self.request.user
        self.request.session["level"] = 20
        return super().form_valid(form)

    def form_invalid(self, form):
        self.request.session["level"] = 50
        return super().form_invalid(form)


class MaisonSupllierExclusionUpdate(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    ...


def exclusion_delete(request):
    ...


def exclusion_export_list(_):
    ...
