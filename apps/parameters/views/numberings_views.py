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
from apps.parameters.excel_outputs.parameters_excel_numberings import excel_liste_numberings
from apps.parameters.models import Counter
from apps.parameters.forms import CounterForm


# ECRANS DES NUMEROTATIONS =========================================================================
class NumberingsList(ListView):
    """View de la liste des Numérotations"""

    model = Counter
    context_object_name = "numberings"
    template_name = "parameters/numberings_list.html"
    extra_context = {"titre_table": "Numérotations"}


class NumberingCreate(ChangeTraceMixin, SuccessMessageMixin, CreateView):
    """CreateView de création des Numérotations"""

    model = Counter
    form_class = CounterForm
    form_class.use_required_attribute = False
    template_name = "parameters/numberings_update.html"
    success_message = "La Numérotation %(name)s a été créé avec success"
    error_message = "La Numérotation %(name)s n'a pu être créé, une erreur c'est produite"

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["create"] = True
        context["chevron_retour"] = reverse("parameters:numberings_list")
        context["titre_table"] = "Création d'une nouvelle Numérotation"
        context["sep_li"] = "- "

        return context

    def form_valid(self, form):
        """Ajout de l'user à la sauvegarde du formulaire"""
        form.instance.created_by = self.request.user
        self.request.session["level"] = 20

        return super().form_valid(form)


class NumberingUpdate(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView pour modification des Numérotations"""

    model = Counter
    form_class = CounterForm
    form_class.use_required_attribute = False
    template_name = "parameters/numberings_update.html"
    success_message = "La Numérotation %(name)s a été modifiée avec success"
    error_message = "La Numérotation %(name)s n'a pu être modifiée, une erreur c'est produite"

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["titre_table"] = "Mise à jour Numérotation"
        context["chevron_retour"] = reverse("parameters:numberings_list")
        context["sep_li"] = "- "

        return super().get_context_data(**context)

    def form_valid(self, form, **kwargs):
        """Ajout de l'user à la sauvegarde du formulaire"""
        form.instance.modified_by = self.request.user
        self.request.session["level"] = 20

        return super().form_valid(form)


def numberings_export_list(_):
    """
    Export Excel de la liste des Numérotations
    :param _: Request Django
    :return: response_file
    """
    try:

        today = pendulum.now()
        file_name = f"LISTING_DES_NUMEROTATIONS_{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"

        return response_file(excel_liste_numberings, file_name, CONTENT_TYPE_EXCEL)

    except:
        LOGGER_EXPORT_EXCEL.exception("view : numberings_export_list")

    return redirect(reverse("parameters:numberings_list"))


@transaction.atomic
def numbering_delete(request):
    """Suppression des Numérotations
    :param request: Request Django
    :return: view
    """

    if not request.is_ajax() and request.method != "POST":
        return redirect("home")

    data = {"success": "ko"}
    id_pk = request.POST.get("pk")

    try:
        numbering = Counter.objects.get(pk=id_pk)

        if not numbering.name == 'generic':
            trace_mark_delete(
                request=request,
                django_model=Counter,
                data_dict={"id": numbering.pk},
                force_delete=True,
            )
            data = {"success": "success"}

        else:
            LOGGER_VIEWS.exception(
                f"numbering_delete, l'user : {request.user.email!r} "
                f"a tenter de supprimer la Numérotation générique"
            )

    except (Counter.DoesNotExist, Exception) as error:
        LOGGER_VIEWS.exception(
            f"views - numbering_delete, l'user : {request.user.email!r} "
            f"a tenter de supprimer une Numérotation inexistante"
            f"\n{error!r}"
        )

    return JsonResponse(data)
