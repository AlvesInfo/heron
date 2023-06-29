# pylint: disable=R0903,E0401,C0103,W0702,W0613,E1101,W1309,W1203
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
from apps.core.bin.encoders import set_base_64_str
from apps.core.functions.functions_http_response import x_accel_exists_file_response
from apps.book.models import Society
from apps.book.forms import SocietyForm


# ECRANS DES TIERS X3 FOURNISSEURS =================================================================
class SocietiesList(ListView):
    """View de la liste des Tiers X3"""

    model = Society
    context_object_name = "societies"
    template_name = "book/societies_list.html"
    extra_context = {"titre_table": "Tiers X3", "in_use": "alls"}
    queryset = Society.objects.all().values(
        "third_party_num",
        "pk",
        "third_party_num",
        "name",
        "is_supplier",
        "is_client",
        "centers_suppliers_indentifier",
        "invoice_entete",
        "siret_number",
    )


class SocietiesInUseList(ListView):
    """View de la liste des Tiers X3, qui ont été utilisés dans les imports ou factures fournisseurs
    ou ceux qui ont été cochés en utilisation
    """

    model = Society
    context_object_name = "societies"
    template_name = "book/societies_list.html"
    extra_context = {
        "titre_table": "Tiers X3",
        "in_use": "in_use",
        "nb_paging": 50,
    }
    queryset = (
        Society.objects.filter(Q(is_client=True) | Q(is_supplier=True))
        .filter(in_use=True)
        .values(
            "third_party_num",
            "pk",
            "third_party_num",
            "name",
            "is_supplier",
            "is_client",
            "centers_suppliers_indentifier",
            "invoice_entete",
            "siret_number"
        )
    )


class SocietyUpdate(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView pour modification des Centrales Filles"""

    model = Society
    form_class = SocietyForm
    form_class.use_required_attribute = False
    template_name = "book/society_update.html"
    success_message = "Le Tiers %(third_party_num)s a été modifiée avec success"
    error_message = "Le Tiers %(third_party_num)s n'a pu être modifiée, une erreur c'est produite"
    extra_context = {}

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context_dict = super().get_context_data(**kwargs)
        pk = self.kwargs.get("pk")
        in_use = self.kwargs.get("in_use")
        context = {
            **context_dict,
            **{
                "chevron_retour": (
                    reverse("book:societies_list")
                    if in_use == "alls"
                    else reverse("book:societies_list_in_use")
                ),
                "titre_table": (
                    f"Mise à jour du Tiers : "
                    f"{context_dict.get('object').third_party_num} - "
                    f"{context_dict.get('object').name}"
                ),
                "compte_banque": (
                    context_dict.get("object").bank_society.filter(is_default=True).first()
                ),
                "third_party_num": context_dict.get("object").third_party_num,
                "pk": context_dict.get("object").pk,
                "url_retour_supplier_cct": set_base_64_str(
                    reverse("book:society_update", args=[pk, in_use])
                ),
            },
        }
        return context

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        in_use = self.kwargs.get("in_use")
        return (
            reverse("book:societies_list")
            if in_use == "alls"
            else reverse("book:societies_list_in_use")
        )

    def form_valid(self, form, **kwargs):
        """
        On surcharge la méthode form_valid, pour ajouter les données, à la vollée,
        de l'adresse par défaut si la checkbox adresse_principale_sage est à true.
        """
        form.instance.modified_by = self.request.user
        self.request.session["level"] = 20

        return super().form_valid(form)


def export_list_societies(_, file_name: str):
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
