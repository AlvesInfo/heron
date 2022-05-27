# pylint: disable=R0903,E0401,C0103,W0702,W0613
"""
Views des Tiers X3
"""
from pathlib import Path

from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import reverse
from django.views.generic import ListView, UpdateView
from django.db.models import Q

from heron.settings import MEDIA_EXCEL_FILES_DIR
from apps.core.functions.functions_http_response import x_accel_exists_file_response
from apps.book.models import Society
from apps.book.forms import SocietyForm


# ECRANS DES FOURNISSEURS ==========================================================================
class SocietiesList(ListView):
    """View de la liste des Tiers X3"""

    model = Society
    context_object_name = "societies"
    template_name = "book/societies_list.html"
    extra_context = {"titre_table": "Tiers X3"}
    queryset = Society.objects.filter(Q(is_client=True) | Q(is_supplier=True))


class SocietyUpdate(SuccessMessageMixin, UpdateView):
    """UpdateView pour modification des Centrales Filles"""

    model = Society
    form_class = SocietyForm
    form_class.use_required_attribute = False
    template_name = "book/society_update.html"
    success_message = "Le Tiers %(third_party_num)s a été modifiée avec success"
    error_message = "Le Tiers %(third_party_num)s n'a pu être modifiée, une erreur c'est produite"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["chevron_retour"] = reverse("book:societies_list")
        context["titre_table"] = (
            f"Mise à jour du Tiers : "
            f"{context.get('object').third_party_num} - "
            f"{context.get('object').name}"
        )
        context["adresse_principale_sage"] = context.get("object").society_society.filter(
            default_adress=True
        ).first()
        return context

    def form_valid(self, form):
        form.instance.modified_by = self.request.user
        copy_default_address = form.cleaned_data.get("copy_default_address")

        if copy_default_address:
            society = form.save()
            adress = self.get_context_data().get("adresse_principale_sage")
            society.immeuble = adress.line_01
            society.adresse = adress.line_02
            society.code_postal = adress.postal_code
            society.ville = adress.city
            society.pays = adress.country
            society.telephone = adress.phone_number_01
            society.mobile = adress.mobile_number
            society.email = adress.email_01
            society.save()

        self.request.session["level"] = 20
        return super().form_valid(form)

    def form_invalid(self, form):
        self.request.session["level"] = 50
        return super().form_invalid(form)


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
    response = x_accel_exists_file_response(file)

    return response
