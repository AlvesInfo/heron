"""Views des Paramètres Nature/Genre."""

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
from apps.parameters.excel_outputs.parameters_excel_natures import excel_liste_natures
from apps.parameters.forms import NatureForm
from apps.parameters.models import Nature
from heron.loggers import LOGGER_EXPORT_EXCEL, LOGGER_VIEWS


# ECRANS DES NATURE/GENRE ==========================================================================
class NaturesList(ListView):
    """View de la liste des Natures."""

    model = Nature
    context_object_name = "natures"
    template_name = "parameters/natures_list.html"
    extra_context = {"titre_table": "Natures/Genre"}


class NatureCreate(ChangeTraceMixin, SuccessMessageMixin, CreateView):
    """CreateView de création des Natures."""

    model = Nature
    form_class = NatureForm
    template_name = "parameters/natures_update.html"
    success_message = "La Nature/Genre %(name)s a été créé avec success"
    error_message = "La Nature/Genre %(name)s n'a pu être créé, une erreur c'est produite"

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template."""
        context = super().get_context_data(**kwargs)
        context["create"] = True
        context["chevron_retour"] = reverse("parameters:natures_list")
        context["titre_table"] = "Création d'une nouvelle Nature/Genre"

        return context

    def form_valid(self, form):
        """Ajout de l'user à la sauvegarde du formulaire."""
        form.instance.created_by = self.request.user
        self.request.session["level"] = 20

        return super().form_valid(form)


class NatureUpdate(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView pour modification des Natures."""

    model = Nature
    form_class = NatureForm
    template_name = "parameters/natures_update.html"
    success_message = "La Nature/Genre %(name)s a été modifiée avec success"
    error_message = "La Nature/Genre %(name)s n'a pu être modifiée, une erreur c'est produite"

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template."""
        context = super().get_context_data(**kwargs)
        context["titre_table"] = "Mise à jour Nature/Genre"
        context["chevron_retour"] = reverse("parameters:natures_list")

        return super().get_context_data(**context)

    def form_valid(self, form):
        """Ajout de l'user à la sauvegarde du formulaire."""
        form.instance.modified_by = self.request.user
        self.request.session["level"] = 20

        return super().form_valid(form)


def natures_export_list(_):
    """Export Excel de la liste des Natures.

    :param _: Request Django
    :return: response_file.
    """
    try:
        today = pendulum.now()
        file_name = f"LISTING_DES_NATURES_GENRE_{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"

        return response_file(excel_liste_natures, file_name, CONTENT_TYPE_EXCEL)

    except Exception:
        LOGGER_EXPORT_EXCEL.exception("view : natures_export_list")

    return redirect(reverse("parameters:natures_list"))


@transaction.atomic
def nature_delete(request):
    """Suppression des Natures.

    :param request: Request Django
    :return: view.
    """
    if not is_ajax(request) or request.method != "POST":
        return redirect("home")

    data = {"success": "ko"}
    id_pk = request.POST.get("pk")

    try:
        nature = Nature.objects.get(pk=id_pk)

        trace_mark_delete(
            request=request,
            django_model=Nature,
            data_dict={"id": nature.pk},
            force_delete=True,
        )
        data = {"success": "success"}

    except (Nature.DoesNotExist, Exception):
        LOGGER_VIEWS.exception(
            "views - nature_delete, l'user : %r a tenter de supprimer une Nature/Genre inexistante",
            request.user.email,
        )

    return JsonResponse(data)
