# pylint: disable=E0401,R0903
"""
Views des Centrales Mères
"""
import pendulum
from django.shortcuts import redirect, reverse
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView, CreateView, UpdateView

from heron.loggers import ERROR_VIEWS_LOGGER
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.centers_purchasing.excel_outputs.output_excel_meres_list import (
    excel_meres_list,
)
from apps.centers_purchasing.models import PrincipalCenterPurchase
from apps.centers_purchasing.forms import MeresForm


# ECRANS DES CENTRALES MERES =======================================================================
class MeresList(ListView):
    """View de la liste des Centrales Mères"""

    model = PrincipalCenterPurchase
    context_object_name = "meres"
    template_name = "centers_purchasing/meres_list.html"
    extra_context = {"titre_table": "Centrales Mères"}


class MereCreate(SuccessMessageMixin, CreateView):
    """CreateView de création des Centrales Mères"""

    model = PrincipalCenterPurchase
    form_class = MeresForm
    form_class.use_required_attribute = False
    template_name = "centers_purchasing/mere_update.html"
    success_message = "La Centrale Mère %(code)s a été créé avec success"
    error_message = "La Centrale Mère %(code)s n'a pu être créé, une erreur c'est produite"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["create"] = True
        context["chevron_retour"] = reverse("centers_purchasing:meres_list")
        context["titre_table"] = "Création d'une nouvelle Centrale Mère"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.modified_by = self.request.user
        self.request.session["level"] = 20
        return super().form_valid(form)

    def form_invalid(self, form):
        self.request.session["level"] = 50
        return super().form_invalid(form)


class MereUpdate(SuccessMessageMixin, UpdateView):
    """UpdateView pour modification des Centrales Mères"""

    model = PrincipalCenterPurchase
    form_class = MeresForm
    form_class.use_required_attribute = False
    template_name = "centers_purchasing/mere_update.html"
    success_message = "La Centrale Mère %(code)s a été modifiée avec success"
    error_message = "La Centrale Mère %(code)s n'a pu être modifiée, une erreur c'est produite"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["chevron_retour"] = reverse("centers_purchasing:meres_list")
        context["titre_table"] = (
            f"Mise à jour de la Centrale Mère : "
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


def meres_export_list(request):
    """
    Export Excel de la liste des Centrales Mères
    :param request: Request Django
    :return: response_file
    """

    try:
        if request.method == "GET":
            today = pendulum.now()
            file_name = (
                f"LISTING_DES_CENTRALES_MERES_{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"
            )

            return response_file(
                excel_meres_list, file_name, CONTENT_TYPE_EXCEL, PrincipalCenterPurchase
            )

    except:
        ERROR_VIEWS_LOGGER.exception("view : meres_export_list")

    return redirect(reverse("centers_purchasing:meres_list"))
