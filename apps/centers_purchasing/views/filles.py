# pylint: disable=E0401,R0903
"""
Views des Centrales Filles
"""
import pendulum
from django.shortcuts import redirect, reverse
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView, CreateView, UpdateView

from heron.loggers import ERROR_VIEWS_LOGGER
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.centers_purchasing.excel_outputs.output_excel_filles_list import (
    excel_filles_list,
)
from apps.centers_purchasing.models import ChildCenterPurchase
from apps.centers_purchasing.forms import FillesForm


# ECRANS DES CENTRALES FILLES ======================================================================
class FillesList(ListView):
    """View de la liste des Centrales Filles"""

    model = ChildCenterPurchase
    context_object_name = "filles"
    template_name = "centers_purchasing/filles_list.html"
    extra_context = {"titre_table": "Centrales Filles"}


class FilleCreate(SuccessMessageMixin, CreateView):
    """CreateView de création des Centrales Filles"""

    model = ChildCenterPurchase
    form_class = FillesForm
    form_class.use_required_attribute = False
    template_name = "centers_purchasing/fille_update.html"
    success_message = "La Centrale Fille %(code)s a été créé avec success"
    error_message = "La Centrale Fille %(code)s n'a pu être créé, une erreur c'est produite"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["create"] = True
        context["chevron_retour"] = reverse("centers_purchasing:filles_list")
        context["titre_table"] = "Création d'une nouvelle Centrale Fille"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.modified_by = self.request.user
        self.request.session["level"] = 20
        return super().form_valid(form)

    def form_invalid(self, form):
        self.request.session["level"] = 50
        return super().form_invalid(form)


class FilleUpdate(SuccessMessageMixin, UpdateView):
    """UpdateView pour modification des Centrales Filles"""

    model = ChildCenterPurchase
    form_class = FillesForm
    form_class.use_required_attribute = False
    template_name = "centers_purchasing/fille_update.html"
    success_message = "La Centrale Fille %(code)s a été modifiée avec success"
    error_message = "La Centrale Fille %(code)s n'a pu être modifiée, une erreur c'est produite"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["chevron_retour"] = reverse("centers_purchasing:filles_list")
        context["titre_table"] = (
            f"Mise à jour de la Centrale Fille : "
            f"{context.get('object').code} - "
            f"{context.get('object').name}"
        )
        return context

    def form_valid(self, form):
        form.instance.modified_by = self.request.user
        self.request.session["level"] = 20
        return super().form_valid(form)

    def form_invalid(self, form):
        self.request.session["level"] = 50
        return super().form_invalid(form)


def filles_export_list(request):
    """
    Export Excel de la liste des Centrales Filles
    :param request: Request Django
    :return: response_file
    """

    try:
        if request.method == "GET":
            today = pendulum.now()
            file_name = (
                f"LISTING_DES_CENTRALES_FILLES_{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"
            )

            return response_file(
                excel_filles_list, file_name, CONTENT_TYPE_EXCEL, ChildCenterPurchase
            )

    except:
        ERROR_VIEWS_LOGGER.exception("view : filles_export_list")

    return redirect(reverse("centers_purchasing:filles_list"))
