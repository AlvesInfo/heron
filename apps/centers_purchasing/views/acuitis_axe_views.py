# pylint: disable=E0401,R0903
"""
FR : Module dictionnaire famille_acuitis - code_rayon_acuitis - axes_pro
EN : acuitis family dictionary module - acuitis radius code - axes_pro

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
from apps.centers_purchasing.excel_outputs.output_excel_acuitis_axe_list import (
    excel_liste_acuitis_axe,
)
from apps.centers_purchasing.models import AxeProFamilleAcuitis
from apps.centers_purchasing.forms import (
    AxeProFamilleAcuitisForm,
    AxeProFamilleAcuitisDeleteForm,
)

# Regroupement factures


class AcuitisAxeList(ListView):
    """View de la liste du dictionnaire famille_acuitis - code_rayon_acuitis - axes_pro"""

    model = AxeProFamilleAcuitis
    context_object_name = "acuitis_axe"
    template_name = "centers_purchasing/acuitis_axe_list.html"
    extra_context = {"titre_table": "Dictionnaire Acuitis famille - code rayon - axes pro"}


class AcuitisAxeCreate(ChangeTraceMixin, SuccessMessageMixin, CreateView):
    """CreateView de création du dictionnaire famille_acuitis - code_rayon_acuitis - axes_pro"""

    model = AxeProFamilleAcuitis
    form_class = AxeProFamilleAcuitisForm
    form_class.use_required_attribute = False
    template_name = "centers_purchasing/acuitis_axe_update.html"
    success_message = (
        "Le dictionnaire famille_acuitis - code_rayon_acuitis - axes_pro a été créé avec success"
    )
    error_message = (
        "Le dictionnaire famille_acuitis - code_rayon_acuitis - axes_pro n'a pu être créé, "
        "une erreur c'est produite"
    )

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["chevron_retour"] = reverse("centers_purchasing:acuitis_axe_list")
        context[
            "titre_table"
        ] = "Création Dictionnaire Acuitis famille - code rayon - axes pro"
        context["create"] = True
        return context

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        return reverse("centers_purchasing:acuitis_axe_list")


class AcuitisAxeUpdate(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView du dictionnaire famille_acuitis - code_rayon_acuitis - axes_pro"""

    model = AxeProFamilleAcuitis
    form_class = AxeProFamilleAcuitisForm
    form_class.use_required_attribute = False
    template_name = "centers_purchasing/acuitis_axe_update.html"
    success_message = (
        "Le dictionnaire famille_acuitis - code_rayon_acuitis - axes_pro a été modifié avec success"
    )
    error_message = (
        "Le dictionnaire famille_acuitis - code_rayon_acuitis - axes_pro n'a pu être modifié, "
        "une erreur c'est produite"
    )

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["chevron_retour"] = reverse("centers_purchasing:acuitis_axe_list")
        context["titre_table"] = (
            "Mise à jour Dictionnaire Acuitis famille - code rayon - axes pro"
        )
        return context

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        return reverse("centers_purchasing:acuitis_axe_list")


def acuitis_axe_delete(request):
    """Vue ajax de suppresion d'une ligne de la table"""

    if not request.is_ajax() and request.method != "POST":
        return redirect("home")

    data = {"success": "ko"}
    id_pk = request.POST.get("pk")
    form = AxeProFamilleAcuitisDeleteForm({"id": id_pk})

    if form.is_valid():
        trace_mark_delete(
            request=request,
            django_model=AxeProFamilleAcuitis,
            data_dict={"id": id_pk},
            force_delete=True,
        )
        data = {"success": "success"}

    else:
        LOGGER_VIEWS.exception(f"acuitis_axe_delete, form invalid : {form.errors!r}")

    return JsonResponse(data)


def acuitis_axe_export_list(_):
    """
    Export Excel du dictionnaire famille_acuitis - code_rayon_acuitis - axes_pro
    :return: response_file
    """
    try:

        today = pendulum.now()
        file_name = (
            f"LISTING_DES_FAMILLES_ACUITIS_AXE_PRO_"
            f"{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"
        )

        return response_file(excel_liste_acuitis_axe, file_name, CONTENT_TYPE_EXCEL)

    except:
        LOGGER_VIEWS.exception("view : acuitis_axe_export_list")

    return redirect(reverse("centers_purchasing:acuitis_axe_list"))
