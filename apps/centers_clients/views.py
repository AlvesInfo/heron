# pylint: disable=E0401,R0903
"""
Views des Maisons
"""

import pendulum
from django.shortcuts import redirect, reverse
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView, UpdateView

from heron.loggers import ERROR_VIEWS_LOGGER
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.centers_clients.excel_outputs.centers_clients_excel_maisons_list import (
    excel_liste_maisons,
)
from apps.centers_clients.models import Maison


# ECRANS DES MAISONS ===============================================================================
class MaisonsList(ListView):
    """View de la liste des Maisons"""

    model = Maison
    context_object_name = "maisons"
    template_name = "centers_clients/maisons_list.html"


def export_list_maisons(request):
    """
    Export Excel de la liste des Sociétés
    :param request: Request Django
    :return: response_file
    """
    if request.method == "POST":
        try:

            today = pendulum.now()
            maisons = Maison

            if "export_list_maisons" in request.POST:
                file_name = (
                    f"LISTING_DES_MAISONS_{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"
                )

            else:
                return redirect(reverse("centers_clients:maisons_list"))

            return response_file(excel_liste_maisons, file_name, CONTENT_TYPE_EXCEL, maisons)

        except:
            ERROR_VIEWS_LOGGER.exception("view : export_list_maisons")

    return redirect(reverse("centers_clients:maisons_list"))
