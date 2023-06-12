# pylint: disable=E0401,R0903
"""
Views des Emails d'envoi
"""
from pathlib import Path

import pendulum
from django.shortcuts import redirect, reverse
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView, CreateView, UpdateView

from heron.loggers import LOGGER_VIEWS
from heron.settings import MEDIA_DIR
from apps.core.bin.change_traces import ChangeTraceMixin
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.parameters.models import Email
from apps.parameters.forms import EmailForm


# ECRANS DES EMAILS ================================================================================


class EmailList(ListView):
    """View de la liste des Emails"""

    model = Email
    context_object_name = "emails"
    template_name = "parameters/emails_list.html"
    extra_context = {"titre_table": "Emails", "nb_paging": 7}


class EmailCreate(ChangeTraceMixin, SuccessMessageMixin, CreateView):
    """CreateView de création des Emails"""

    model = Email
    form_class = EmailForm
    form_class.use_required_attribute = False
    template_name = "parameters/email_update.html"
    success_message = "L'email %(name)s a été créé avec success"
    error_message = "L'email %(name)s n'a pu être créé, une erreur c'est produite"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["create"] = True
        context["chevron_retour"] = reverse("parameters:emails_list")
        context["titre_table"] = "Création d'un nouvel email type"

        return context

    def form_valid(self, form):
        """On surcharge la méthode form_valid"""
        self.request.session["level"] = 20

        return super().form_valid(form)


class EmailUpdate(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView pour modification des Emails"""

    model = Email
    context_object_name = "email"
    form_class = EmailForm
    form_class.use_required_attribute = False
    template_name = "parameters/email_update.html"
    success_message = "L'email %(name)s a été modifiée avec success"
    error_message = "L'email %(name)s n'a pu être modifiée, une erreur c'est produite"

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["chevron_retour"] = reverse("parameters:emails_list")
        context["titre_table"] = f"Mise à jour de l'email : {context.get('object').name}"

        return context

    def form_valid(self, form):
        """On surcharge la méthode form_valid"""
        self.request.session["level"] = 20

        return super().form_valid(form)
