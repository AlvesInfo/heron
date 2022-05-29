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
from apps.core.bin.change_traces import ChangeTraceMixin
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


class SocietyUpdate(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView pour modification des Centrales Filles"""

    model = Society
    form_class = SocietyForm
    form_class.use_required_attribute = False
    template_name = "book/society_update.html"
    success_message = "Le Tiers %(third_party_num)s a été modifiée avec success"
    error_message = "Le Tiers %(third_party_num)s n'a pu être modifiée, une erreur c'est produite"

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["chevron_retour"] = reverse("book:societies_list")
        context["titre_table"] = (
            f"Mise à jour du Tiers : "
            f"{context.get('object').third_party_num} - "
            f"{context.get('object').name}"
        )
        context["adresse_principale_sage"] = (
            context.get("object").society_society.filter(default_adress=True).first()
        )
        return context

    def form_valid(self, form, **kwargs):
        """
        On surcharge la méthode form_valid, pour ajouter les données, à la vollée,
        de l'adresse par défaut si la checkbox adresse_principale_sage est à true
        et ajouter le niveau de message et sa couleur.
        """
        copy_default_address = form.cleaned_data.get("copy_default_address")

        if copy_default_address:
            adress = self.get_context_data().get("adresse_principale_sage")
            if adress:
                self.object.immeuble = adress.line_01
                self.object.adresse = adress.line_02
                self.object.code_postal = adress.postal_code
                self.object.ville = adress.city
                self.object.pays = adress.country
                self.object.telephone = adress.phone_number_01
                self.object.mobile = adress.mobile_number
                self.object.email = adress.email_01
                self.object.save()

        return super().form_valid(form)


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
