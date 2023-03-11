# pylint: disable=E0401,R0903,W0201,W0702,W0613,W1203
"""
Views des Pays Maisons à écarter par founisseurs

Commentaire:

created at: 2023-01-20
created by: Paulo ALVES

modified at: 2023-01-20
modified by: Paulo ALVES
"""
import pendulum
from django.http import JsonResponse
from django.shortcuts import redirect, reverse
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView, CreateView, UpdateView

from heron.loggers import LOGGER_VIEWS
from apps.core.bin.change_traces import ChangeTraceMixin, trace_mark_delete
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.centers_clients.excel_outputs.excel_exclusions_tiers_pays_clients_list import (
    excel_liste_exclusion_pays,
)
from apps.centers_clients.models import SupllierCountryExclusion
from apps.centers_clients.forms import (
    SupllierCountryExclusionForm,
    SupllierCountryExclusionDeleteForm,
)


class CountryMaisonSupllierExclusionList(ListView):
    """View de la liste des Tiers X3/Pays Clients"""

    model = SupllierCountryExclusion
    context_object_name = "exclusions"
    template_name = "centers_clients/exclusions_pays_list.html"
    extra_context = {"titre_table": "Couples d'exclusion Tiers X3/Pays Client"}


class CountryMaisonSupllierExclusionCreate(ChangeTraceMixin, SuccessMessageMixin, CreateView):
    """CreateView de création des couples Tiers X3/Pays Clients à exlucre de la facturation"""

    model = SupllierCountryExclusion
    form_class = SupllierCountryExclusionForm
    form_class.use_required_attribute = False
    template_name = "centers_clients/exclusion_pays_update.html"
    success_message = (
        "Le couple d'exclusion, %(third_party_num)s - %(country)s a été créé avec success"
    )
    error_message = (
        "Le couple d'exclusion, %(third_party_num)s - %(country)s n'a pu être créé, "
        "une erreur c'est produite"
    )

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["chevron_retour"] = reverse("centers_clients:exclusions_country_list")
        context["titre_table"] = "Création d'un nouveau couple d'exclusion Tiers X3/Pays Clients"
        return context

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        return reverse("centers_clients:exclusions_country_list")

    def form_valid(self, form):
        """Ajout de l'user à la sauvegarde du formulaire"""
        form.instance.created_by = self.request.user
        self.request.session["level"] = 20
        return super().form_valid(form)


class CountryMaisonSupllierExclusionUpdate(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView de création des couples Tiers X3/Pays Clients à exlucre de la facturation"""

    model = SupllierCountryExclusion
    form_class = SupllierCountryExclusionForm
    form_class.use_required_attribute = False
    template_name = "centers_clients/exclusion_pays_update.html"
    success_message = (
        "Le couple d'exclusion, %(third_party_num)s - %(country)s a été modifié avec success"
    )
    error_message = (
        "Le couple d'exclusion, %(third_party_num)s - %(country)s n'a pu être modifié, "
        "une erreur c'est produite"
    )

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["chevron_retour"] = reverse("centers_clients:exclusions_country_list")
        context["titre_table"] = "Création d'un nouveau couple d'exclusion Tiers X3/Client"
        return context

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        return reverse("centers_clients:exclusions_country_list")

    def form_valid(self, form, **kwargs):
        """Ajout de l'user à la sauvegarde du formulaire"""
        form.instance.modified_by = self.request.user
        self.request.session["level"] = 20
        return super().form_valid(form)


def exclusion_country_delete(request):

    if not request.is_ajax() and request.method != "POST":
        return redirect("home")

    data = {"success": "ko"}
    id_pk = request.POST.get("pk")
    form = SupllierCountryExclusionDeleteForm({"id": id_pk})

    if form.is_valid():
        trace_mark_delete(
            request=request,
            django_model=SupllierCountryExclusion,
            data_dict={"id": id_pk},
            force_delete=True,
        )
        data = {"success": "success"}

    else:
        LOGGER_VIEWS.exception(f"delete_invoice_purchase, form invalid : {form.errors!r}")

    return JsonResponse(data)


def exclusion_country_export_list(_):
    """
    Export Excel de la liste des couples Tiers X3/Pays Clients à exlucre de la facturation
    :return: response_file
    """
    try:

        today = pendulum.now()
        file_name = (
            f"LISTING_DES_EXCLUSIONS_TIERS_PAYS_CLIENTS_"
            f"{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"
        )

        return response_file(excel_liste_exclusion_pays, file_name, CONTENT_TYPE_EXCEL)

    except:
        LOGGER_VIEWS.exception("view : export_list_societies")

    return redirect(reverse("book:societies_list"))
