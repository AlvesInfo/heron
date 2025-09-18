# pylint: disable=E0401,R0903
"""
FR : View Entêtes détails de facturation
EN : View Billing Details Headers

Commentaire:

created at: 2023-03-21
created by: Paulo ALVES

modified at: 2023-03-21
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
from apps.invoices.excel_outputs.output_excel_axes_details_list import (
    excel_liste_axes_details,
)
from apps.invoices.excel_outputs.output_excel_entetes_details_list import (
    excel_liste_entetes_details,
)
from apps.invoices.models import EnteteDetails, AxesDetails
from apps.invoices.forms import (
    EnteteDetailsForm,
    EnteteDetailsDeleteForm,
    AxesDetailsForm,
    AxesDetailsDeleteForm,
)

# Entêtes des détails de facturation


class EntetesDetailsList(ListView):
    """View de la liste du Dictionnaire Entêtes Détails de facturation"""

    model = EnteteDetails
    context_object_name = "entetes_details"
    template_name = "invoices/entetes_details_list.html"
    extra_context = {"titre_table": "Dictionnaire Entêtes Détails de facturation"}


class EntetesDetailsCreate(ChangeTraceMixin, SuccessMessageMixin, CreateView):
    """CreateView de création du Dictionnaire Entêtes Détails de facturation"""

    model = EnteteDetails
    form_class = EnteteDetailsForm
    form_class.use_required_attribute = False
    template_name = "invoices/entetes_details_update.html"
    success_message = "Le Dictionnaire Entêtes Détails de facturation a été créé avec success"
    error_message = (
        "Le Dictionnaire Entêtes Détails de facturation n'a pu être créé, "
        "une erreur c'est produite"
    )

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["chevron_retour"] = reverse("invoices:entete_details_list")
        context["titre_table"] = "Création d'une nouvelle Entêtes Détails de facturation"
        return context

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        return reverse("invoices:entete_details_list")

    def form_valid(self, form):
        """Ajout de l'user à la sauvegarde du formulaire"""
        form.instance.created_by = self.request.user
        self.request.session["level"] = 20

        return super().form_valid(form)


class EntetesDetailsUpdate(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView d'update du Dictionnaire Entêtes Détails de facturation"""

    model = EnteteDetails
    form_class = EnteteDetailsForm
    form_class.use_required_attribute = False
    template_name = "invoices/entetes_details_update.html"
    success_message = (
        "Le dictionnaire Entêtes Détails de facturation a été modifié avec success"
    )
    error_message = (
        "Le dictionnaire Entêtes Détails de facturation n'a pu être modifié, "
        "une erreur c'est produite"
    )

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["chevron_retour"] = reverse("invoices:entete_details_list")
        context["titre_table"] = "Mise à jour d'une Entêtes Détails de facturation"
        return context

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        return reverse("invoices:entete_details_list")

    def form_valid(self, form, **kwargs):
        """Ajout de l'user à la sauvegarde du formulaire"""
        form.instance.modified_by = self.request.user
        self.request.session["level"] = 20

        return super().form_valid(form)


def entetes_details_delete(request):
    """Vue ajax de suppresion d'une ligne de la table"""

    if not request.is_ajax() and request.method != "POST":
        return redirect("home")

    data = {"success": "ko"}
    id_pk = request.POST.get("pk")
    form = EnteteDetailsDeleteForm({"id": id_pk})

    if form.is_valid():
        trace_mark_delete(
            request=request,
            django_model=EnteteDetails,
            data_dict={"id": id_pk},
            force_delete=True,
        )
        data = {"success": "success"}

    else:
        LOGGER_VIEWS.exception(f"entetes_details_delete, form invalid : {form.errors!r}")

    return JsonResponse(data)


def entetes_details_export_list(_):
    """
    Export Excel de la liste du Dictionnaire Entêtes Détails de facturation
    :return: response_file
    """
    try:

        today = pendulum.now()
        file_name = (
            f"LISTING_DES_ENTETES_DETAILS_DE_FACTURATION_"
            f"{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"
        )

        return response_file(excel_liste_entetes_details, file_name, CONTENT_TYPE_EXCEL)

    except:
        LOGGER_VIEWS.exception("view : entetes_details_export_list")

    return redirect(reverse("invoices:entete_details_list"))


# Module Dictionnaire Axe Pro/Entêtes de détails de facturation


class AxesDetailsList(ListView):
    """View de la liste du Dictionnaire Axe Pro/Détails de facturation"""

    model = AxesDetails
    context_object_name = "axes_details"
    template_name = "invoices/axes_details_list.html"
    extra_context = {"titre_table": "Dictionnaire Axe Pro/Détails de facturation"}


class AxesDetailsCreate(ChangeTraceMixin, SuccessMessageMixin, CreateView):
    """CreateView de création du Dictionnaire Axe Pro/Détails de facturation"""

    model = AxesDetails
    form_class = AxesDetailsForm
    form_class.use_required_attribute = False
    template_name = "invoices/axes_details_update.html"
    success_message = "Le Dictionnaire Axe Pro/Détails de facturation a été créé avec success"
    error_message = (
        "Le Dictionnaire Axe Pro/Détails de facturation n'a pu être créé, "
        "une erreur c'est produite"
    )

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["chevron_retour"] = reverse("invoices:axes_details_list")
        context["titre_table"] = "Création d'un nouvel Axe Pro/Détails de facturation"
        return context

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        return reverse("invoices:axes_details_list")

    def form_valid(self, form):
        """Ajout de l'user à la sauvegarde du formulaire"""
        form.instance.created_by = self.request.user
        self.request.session["level"] = 20

        return super().form_valid(form)


class AxesDetailsUpdate(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView d'update du Dictionnaire Axe Pro/Détails de facturation"""

    model = AxesDetails
    form_class = AxesDetailsForm
    form_class.use_required_attribute = False
    template_name = "invoices/axes_details_update.html"
    success_message = (
        "Le dictionnaire Axe Pro/Détails de facturation a été modifié avec success"
    )
    error_message = (
        "Le dictionnaire Axe Pro/Détails de facturation n'a pu être modifié, "
        "une erreur c'est produite"
    )

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["chevron_retour"] = reverse("invoices:axes_details_list")
        context["titre_table"] = "Mise à jour d'un Axe Pro/Détails de facturation"
        return context

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        return reverse("invoices:axes_details_list")

    def form_valid(self, form, **kwargs):
        """Ajout de l'user à la sauvegarde du formulaire"""
        form.instance.modified_by = self.request.user
        self.request.session["level"] = 20

        return super().form_valid(form)


def axes_details_delete(request):
    """Vue ajax de suppresion d'une ligne de la table"""

    if not request.is_ajax() and request.method != "POST":
        return redirect("home")

    data = {"success": "ko"}
    id_pk = request.POST.get("pk")
    form = AxesDetailsDeleteForm({"id": id_pk})

    if form.is_valid():
        trace_mark_delete(
            request=request,
            django_model=AxesDetails,
            data_dict={"id": id_pk},
            force_delete=True,
        )
        data = {"success": "success"}

    else:
        LOGGER_VIEWS.exception(f"axes_details_delete, form invalid : {form.errors!r}")

    return JsonResponse(data)


def axes_details_export_list(_):
    """
    Export Excel de la liste du Dictionnaire Axe Pro/Détails de facturation
    :return: response_file
    """
    try:

        today = pendulum.now()
        file_name = (
            f"LISTING_DES_AXE_PRO_DETAILS_DE_FACTURATION_"
            f"{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"
        )

        return response_file(excel_liste_axes_details, file_name, CONTENT_TYPE_EXCEL)

    except:
        LOGGER_VIEWS.exception("view : axes_details_export_list")

    return redirect(reverse("invoices:axes_details_list"))
