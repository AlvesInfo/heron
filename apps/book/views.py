# pylint: disable=R0903,E0401,C0103,W0702
"""
Views des Tiers X3
"""

import pendulum
from django.shortcuts import render, redirect, reverse
from django.views.generic import ListView

from heron.loggers import ERROR_VIEWS_LOGGER
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.book.excel_outputs.book_excel_societies_list import excel_liste_societies
from apps.book.models import Society


# ECRANS DES FOURNISSEURS ==========================================================================
class SocietiesList(ListView):
    """View de la liste des Tiers X3"""

    model = Society
    context_object_name = "societies"
    template_name = "book/societies_list.html"
    extra_context = {"titre_table": "Tiers X3"}


def society_view(request, pk):
    """Vue en table d'une société"""

    society = Society.objects.get(pk=pk)
    context = {
        "society": society,
        "chevron_retour": reverse("book:societies_list"),
        "titre_table": f"{society.third_party_num} - {society.name}",
    }

    return render(request, "book/society_view.html", context=context)


def export_list_societies(request):
    """
    Export Excel de la liste des Sociétés
    :param request: Request Django
    :return: response_file
    """

    if request.method == "POST":
        try:

            today = pendulum.now()
            societies = Society

            if "export_list_societies" in request.POST:
                society_type = "tiers"
                file_name = f"LISTING_DES_TIERS_{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"

            elif "export_list_clients" in request.POST:
                society_type = "clients"
                file_name = (
                    f"LISTING_DES_CLIENTS_{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"
                )

            elif "export_list_supplierss" in request.POST:
                society_type = "suppliers"
                file_name = (
                    f"LISTING_DES_FOURNISSEURS_{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"
                )

            else:
                return redirect(reverse("book:societies_list"))

            return response_file(
                excel_liste_societies, file_name, CONTENT_TYPE_EXCEL, societies, society_type
            )

        except:
            ERROR_VIEWS_LOGGER.exception("view : export_list_societies")

    return redirect(reverse("book:societies_list"))
