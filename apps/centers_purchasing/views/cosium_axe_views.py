# pylint: disable=E0401,R0903,R0901,W1203,W0702
"""
FR : Module dictionnaire code_famille_cosium - axes_pro
EN : Dictionary module code_famille_cosium - axes_pro

Commentaire:

created at: 2023-01-21
created by: Paulo ALVES

modified at: 2023-01-21
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
from apps.centers_purchasing.excel_outputs.output_excel_cosium_axe_list import (
    excel_liste_cosium_axe,
)
from apps.centers_purchasing.models import AxeProFamilleCosium
from apps.centers_purchasing.forms import (
    AxeProFamilleCosiumForm,
    AxeProFamilleCosiumDeleteForm,
)

# Regroupement factures


class CosiumAxeList(ListView):
    """View de la liste du dictionnaire code_famille_cosium - axes_pro"""

    model = AxeProFamilleCosium
    context_object_name = "cosium_axe"
    template_name = "centers_purchasing/cosium_axe_list.html"
    extra_context = {"titre_table": "Dictionnaire Cosium code famille - axes pro"}


class CosiumAxeCreate(ChangeTraceMixin, SuccessMessageMixin, CreateView):
    """CreateView de création du dictionnaire code_famille_cosium - axes_pro"""

    model = AxeProFamilleCosium
    form_class = AxeProFamilleCosiumForm
    form_class.use_required_attribute = False
    template_name = "centers_purchasing/cosium_axe_update.html"
    success_message = "Le dictionnaire code_famille_cosium - axes_pro a été créé avec success"
    error_message = (
        "Le dictionnaire code_famille_cosium - axes_pro n'a pu être créé, "
        "une erreur c'est produite"
    )

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["chevron_retour"] = reverse("centers_purchasing:cosium_axe_list")
        context["titre_table"] = "Création dictionnaire Cosium code famille - axes pro"
        context["create"] = True
        return context

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        return reverse("centers_purchasing:cosium_axe_list")


class CosiumAxeUpdate(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView du dictionnaire code_famille_cosium - axes_pro"""

    model = AxeProFamilleCosium
    form_class = AxeProFamilleCosiumForm
    form_class.use_required_attribute = False
    template_name = "centers_purchasing/cosium_axe_update.html"
    success_message = "Le dictionnaire code_famille_cosium - axes_pro a été modifié avec success"
    error_message = (
        "Le dictionnaire code_famille_cosium - axes_pro n'a pu être modifié, "
        "une erreur c'est produite"
    )

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["chevron_retour"] = reverse("centers_purchasing:cosium_axe_list")
        context["titre_table"] = "Mise à jour dictionnaire Cosium code famille - axes pro"
        return context

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        return reverse("centers_purchasing:cosium_axe_list")


def cosium_axe_delete(request):
    """Vue ajax de suppresion d'une ligne de la table"""

    if not request.is_ajax() and request.method != "POST":
        return redirect("home")

    data = {"success": "ko"}
    id_pk = request.POST.get("pk")
    form = AxeProFamilleCosiumDeleteForm({"id": id_pk})

    if form.is_valid():
        trace_mark_delete(
            request=request,
            django_model=AxeProFamilleCosium,
            data_dict={"id": id_pk},
            force_delete=True,
        )
        data = {"success": "success"}

    else:
        LOGGER_VIEWS.exception(f"cosium_axe_delete, form invalid : {form.errors!r}")

    return JsonResponse(data)


def cosium_axe_export_list(_):
    """
    Export Excel du dictionnaire code_famille_cosium - axes_pro
    :return: response_file
    """
    try:

        today = pendulum.now()
        file_name = (
            f"LISTING_DES_FAMILLES_COSIUM_AXE_PRO_"
            f"{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"
        )

        return response_file(excel_liste_cosium_axe, file_name, CONTENT_TYPE_EXCEL)

    except:
        LOGGER_VIEWS.exception("view : cosium_axe_export_list")

    return redirect(reverse("centers_purchasing:cosium_axe_list"))
