# pylint: disable=E0401,R0903
"""
Views des Enseignes
"""
from pathlib import Path

import pendulum
from django.shortcuts import redirect, reverse
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView, CreateView, UpdateView

from heron.loggers import ERROR_VIEWS_LOGGER
from heron.settings import MEDIA_DIR
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.centers_purchasing.excel_outputs.output_excel_enseignes_list import (
    excel_enseignes_list,
)
from apps.centers_purchasing.models import Signboard
from apps.centers_purchasing.forms import SignboardForm


# ECRANS DES CENTRALES FILLES ======================================================================
class EnseignesList(ListView):
    """View de la liste des Enseignes"""

    model = Signboard
    context_object_name = "enseignes"
    template_name = "centers_purchasing/enseignes_list.html"
    extra_context = {"titre_table": "Enseignes"}


class EnseigneCreate(SuccessMessageMixin, CreateView):
    """CreateView de création des Enseignes"""

    model = Signboard
    form_class = SignboardForm
    form_class.use_required_attribute = False
    template_name = "centers_purchasing/enseigne_update.html"
    success_message = "L'Enseigne %(code)s a été créé avec success"
    error_message = "L'Enseigne %(code)s n'a pu être créé, une erreur c'est produite"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["create"] = True
        context["chevron_retour"] = reverse("centers_purchasing:enseignes_list")
        context["titre_table"] = "Création d'une nouvelle Enseigne"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.modified_by = self.request.user
        self.request.session["level"] = 20
        return super().form_valid(form)

    def form_invalid(self, form):
        self.request.session["level"] = 50
        return super().form_invalid(form)


class EnseigneUpdate(SuccessMessageMixin, UpdateView):
    """UpdateView pour modification des Enseignes"""

    model = Signboard
    context_object_name = "enseigne"
    form_class = SignboardForm
    form_class.use_required_attribute = False
    template_name = "centers_purchasing/enseigne_update.html"
    success_message = "L'Enseigne %(code)s a été modifiée avec success"
    error_message = "L'Enseigne %(code)s n'a pu être modifiée, une erreur c'est produite"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["chevron_retour"] = reverse("centers_purchasing:enseignes_list")
        context["titre_table"] = (
            f"Mise à jour de la Enseigne : "
            f"{context.get('object').code} - "
            f"{context.get('object').name}"
        )
        return context

    def form_valid(self, form):
        form.instance.modified_by = self.request.user
        self.request.session["level"] = 20

        if form.data.get("img_delete"):
            form.instance.logo = None

        form.save()

        # On supprime les fichiers qui sont devenus orphelins
        logo_files_path = {
            Signboard._meta.get_field("logo").upload_to + file.name
            for file in (Path(MEDIA_DIR) / Signboard._meta.get_field("logo").upload_to).glob("*")
        }
        logo_files_model = {
            row.get("logo") for row in Signboard.objects.all().values("logo") if row.get("logo")
        }

        for file_path in logo_files_path.difference(logo_files_model):
            file_to_delete = Path(MEDIA_DIR) / file_path
            file_to_delete.unlink()

        return super().form_valid(form)

    def form_invalid(self, form):
        self.request.session["level"] = 50
        return super().form_invalid(form)


def enseignes_export_list(request):
    """
    Export Excel de la liste des Enseignes
    :param request: Request Django
    :return: response_file
    """

    try:
        if request.method == "GET":
            today = pendulum.now()
            file_name = (
                f"LISTING_DES_CENTRALES_FILLES_{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"
            )

            return response_file(excel_enseignes_list, file_name, CONTENT_TYPE_EXCEL, Signboard)

    except:
        ERROR_VIEWS_LOGGER.exception("view : enseignes_export_list")

    return redirect(reverse("centers_purchasing:enseignes_list"))
