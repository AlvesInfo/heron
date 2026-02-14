"""
Views des fmailles clients

Commentaire:

created at: 2026-02-14
created by: Paulo ALVES

modified at: 2026-02-14
modified by: Paulo ALVES
"""
import pendulum
from django.http import JsonResponse
from django.shortcuts import redirect, reverse
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView, CreateView, UpdateView

from heron.loggers import LOGGER_VIEWS
from apps.core.bin.change_traces import ChangeTraceMixin, trace_mark_delete
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.centers_clients.excel_outputs.excel_client_familly_list import (
    excel_client_familly,
)
from apps.centers_clients.models import ClientFamilly
from apps.centers_clients.forms import (
    ClientFamillyForm,
    ClientFamillyDeleteForm,
)

CLIENT_FAMILLY_LIST = "centers_clients:client_familly_list"


class ClientFamillyList(ListView):
    """View de la liste des Familles Client"""

    model = ClientFamilly
    context_object_name = "famillies"
    template_name = "centers_clients/client_familly_list.html"
    extra_context = {"titre_table": "Familles Client"}


class ClientFamillyCreate(ChangeTraceMixin, SuccessMessageMixin, CreateView):
    """CreateView de création des Familles Client"""

    model = ClientFamilly
    form_class = ClientFamillyForm
    form_class.use_required_attribute = False
    template_name = "centers_clients/client_familly_update.html"
    success_message = "La famille %(name)s, a été créé avec success"
    error_message = "La famille %(name)s, n'a pu être créé,  une erreur c'est produite"

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["chevron_retour"] = reverse(CLIENT_FAMILLY_LIST)
        context["titre_table"] = "Création d'une nouvelle Famille Client"
        return context

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        return reverse(CLIENT_FAMILLY_LIST)

    def form_valid(self, form):
        """Ajout de l'user à la sauvegarde du formulaire"""
        form.instance.created_by = self.request.user
        self.request.session["level"] = 20

        return super().form_valid(form)


class ClientFamillyUpdate(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView de modification des Familles Client"""

    model = ClientFamilly
    form_class = ClientFamillyForm
    form_class.use_required_attribute = False
    template_name = "centers_clients/client_familly_update.html"
    success_message = "La famille %(name)s, a été modifiée avec success"
    error_message = "La famille %(name)s, n'a pu être modifiée,  une erreur c'est produite"

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["chevron_retour"] = reverse(CLIENT_FAMILLY_LIST)
        context["titre_table"] = "Mise à jour d'une nouvelle Famille Client"
        return context

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        return reverse(CLIENT_FAMILLY_LIST)

    def form_valid(self, form, **kwargs):
        """Ajout de l'user à la sauvegarde du formulaire"""
        form.instance.modified_by = self.request.user
        self.request.session["level"] = 20

        return super().form_valid(form)


def client_familly_delete(request):

    if not request.is_ajax() and request.method != "POST":
        return redirect("home")

    data = {"success": "ko"}
    id_pk = request.POST.get("pk")
    form = ClientFamillyDeleteForm({"id": id_pk})

    if form.is_valid():
        trace_mark_delete(
            request=request,
            django_model=ClientFamilly,
            data_dict={"id": id_pk},
            force_delete=True,
        )
        data = {"success": "success"}

    else:
        LOGGER_VIEWS.exception(f"client_familly_delete, form invalid : {form.errors!r}")

    return JsonResponse(data)


def export_client_familly_list(_):
    """
    Export Excel de la liste des couples Tiers X3/Pays Clients à exlucre de la facturation
    :return: response_file
    """
    try:

        today = pendulum.now()
        file_name = (
            f"LISTING_DES_FAMILLES_CLIENTS_"
            f"{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"
        )

        return response_file(excel_client_familly, file_name, CONTENT_TYPE_EXCEL)

    except Exception as error:
        LOGGER_VIEWS.exception(f"view : export_client_familly_list: {error!r}")

    return redirect(reverse(CLIENT_FAMILLY_LIST))
