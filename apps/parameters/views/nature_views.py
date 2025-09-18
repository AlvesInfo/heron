# pylint: disable=E0401,R0901,W0702,E1101,W0201,W1203
"""
Views des Paramètres Nature/Genre
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
from apps.parameters.excel_outputs.parameters_excel_natures import excel_liste_natures
from apps.parameters.models import Nature
from apps.parameters.forms import NatureForm


# ECRANS DES NATURE/GENRE ==========================================================================
class NaturesList(ListView):
    """View de la liste des Natures"""

    model = Nature
    context_object_name = "natures"
    template_name = "parameters/natures_list.html"
    extra_context = {"titre_table": "Natures/Genre"}


class NatureCreate(ChangeTraceMixin, SuccessMessageMixin, CreateView):
    """CreateView de création des Natures"""

    model = Nature
    form_class = NatureForm
    form_class.use_required_attribute = False
    template_name = "parameters/natures_update.html"
    success_message = "La Nature/Genre %(name)s a été créé avec success"
    error_message = "La Nature/Genre %(name)s n'a pu être créé, une erreur c'est produite"

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["create"] = True
        context["chevron_retour"] = reverse("parameters:natures_list")
        context["titre_table"] = "Création d'une nouvelle Nature/Genre"

        return context

    def form_valid(self, form):
        """Ajout de l'user à la sauvegarde du formulaire"""
        form.instance.created_by = self.request.user
        self.request.session["level"] = 20

        return super().form_valid(form)


class NatureUpdate(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView pour modification des Natures"""

    model = Nature
    form_class = NatureForm
    form_class.use_required_attribute = False
    template_name = "parameters/natures_update.html"
    success_message = "La Nature/Genre %(name)s a été modifiée avec success"
    error_message = "La Nature/Genre %(name)s n'a pu être modifiée, une erreur c'est produite"

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["titre_table"] = "Mise à jour Nature/Genre"
        context["chevron_retour"] = reverse("parameters:natures_list")

        return super().get_context_data(**context)

    def form_valid(self, form, **kwargs):
        """Ajout de l'user à la sauvegarde du formulaire"""
        form.instance.modified_by = self.request.user
        self.request.session["level"] = 20

        return super().form_valid(form)


def natures_export_list(_):
    """
    Export Excel de la liste des Natures
    :param _: Request Django
    :return: response_file
    """
    try:

        today = pendulum.now()
        file_name = f"LISTING_DES_NATURES_GENRE_{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"

        return response_file(excel_liste_natures, file_name, CONTENT_TYPE_EXCEL)

    except:
        LOGGER_EXPORT_EXCEL.exception("view : natures_export_list")

    return redirect(reverse("parameters:natures_list"))


@transaction.atomic
def nature_delete(request):
    """Suppression des Natures
    :param request: Request Django
    :return: view
    """

    if not request.is_ajax() and request.method != "POST":
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

    except (Nature.DoesNotExist, Exception) as error:
        LOGGER_VIEWS.exception(
            f"views - nature_delete, l'user : {request.user.email!r} "
            f"a tenter de supprimer une Nature/Genre inexistante"
            f"\n{error!r}"
        )

    return JsonResponse(data)
