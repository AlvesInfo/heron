# pylint: disable=R0903,E0401,C0103,W0702,W0613
"""
Views des Tiers X3
"""
from pathlib import Path

from django.shortcuts import render, reverse
from django.views.generic import ListView

from heron.settings import MEDIA_EXCEL_FILES_DIR
from apps.core.functions.functions_http_response import x_accel_redirect_response
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

    society = Society.objects.get(third_party_num=pk)
    context = {
        "society": society,
        "chevron_retour": reverse("book:societies_list"),
        "titre_table": f"{society.third_party_num} - {society.name}",
    }

    return render(request, "book/society_view.html", context=context)


def export_list_societies(request, file_name: str):
    """
    Export Excel de la liste des Sociétés
    :param request: Request Django
    :param file_name: Nom du fichier à downloader
    :return: response_file
    """
    file_dict = {
        "export_list_societies": "LISTING_DES_TIERS.xlsx",
        "export_list_clients": "LISTING_DES_CLIENTS.xlsx",
        "export_list_suppliers": "LISTING_DES_FOURNISSEURS.xlsx",
    }
    file = Path(MEDIA_EXCEL_FILES_DIR) / file_dict.get(file_name)
    response = x_accel_redirect_response(file)

    return response
