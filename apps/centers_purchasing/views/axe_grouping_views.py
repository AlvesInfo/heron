# pylint: disable=E0401,R0903
"""
FR : Module Dictionnaire Axe Pro/Regroupement de facturation
EN : Ax Pro Dictionary/Billing Consolidation Module

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
from apps.centers_purchasing.excel_outputs.output_excel_axe_grouping_list import (
    excel_liste_axe_grouping,
)
from apps.centers_purchasing.models import AxeProGroupingGoods
from apps.centers_purchasing.forms import (
    AxeProGroupingGoodsForm,
    AxeProGroupingGoodsDeleteForm,
)

# Module Dictionnaire Axe Pro/Regroupement de facturation


class AxeGroupingList(ListView):
    """View de la liste du Dictionnaire Axe Pro/Regroupement de facturation"""

    model = AxeProGroupingGoods
    context_object_name = "axes_groupings"
    template_name = "centers_purchasing/axe_grouping_list.html"
    extra_context = {"titre_table": "Dictionnaire Axe Pro/Regroupement de facturation"}


class AxeGroupingCreate(ChangeTraceMixin, SuccessMessageMixin, CreateView):
    """CreateView de création du Dictionnaire Axe Pro/Regroupement de facturation"""

    model = AxeProGroupingGoods
    form_class = AxeProGroupingGoodsForm
    form_class.use_required_attribute = False
    template_name = "centers_purchasing/axe_grouping_update.html"
    success_message = "Le dictionnaire Axe Pro/Regroupement de facturation a été créé avec success"
    error_message = (
        "Le Dictionnaire Axe Pro/Regroupement de facturation n'a pu être créé, "
        "une erreur c'est produite"
    )

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["chevron_retour"] = reverse("centers_purchasing:axe_grouping_list")
        context["titre_table"] = "Création d'un nouveau regroupement de facturation"
        return context

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        return reverse("centers_purchasing:axe_grouping_list")


class AxeGroupingUpdate(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView d'update du Dictionnaire Axe Pro/Regroupement de facturation"""

    model = AxeProGroupingGoods
    form_class = AxeProGroupingGoodsForm
    form_class.use_required_attribute = False
    template_name = "centers_purchasing/axe_grouping_update.html"
    success_message = (
        "Le dictionnaire Axe Pro/Regroupement de facturation a été modifié avec success"
    )
    error_message = (
        "Le dictionnaire Axe Pro/Regroupement de facturation n'a pu être modifié, "
        "une erreur c'est produite"
    )

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["chevron_retour"] = reverse("centers_purchasing:axe_grouping_list")
        context["titre_table"] = "Mise à jour d'un regroupement de facturation"
        return context

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        return reverse("centers_purchasing:axe_grouping_list")


def axe_grouping_delete(request):
    """Vue ajax de suppresion d'une ligne de la table"""

    if not request.is_ajax() and request.method != "POST":
        return redirect("home")

    data = {"success": "ko"}
    id_pk = request.POST.get("pk")
    form = AxeProGroupingGoodsDeleteForm({"id": id_pk})

    if form.is_valid():
        trace_mark_delete(
            request=request,
            django_model=AxeProGroupingGoods,
            data_dict={"id": id_pk},
            force_delete=True,
        )
        data = {"success": "success"}

    else:
        LOGGER_VIEWS.exception(f"axe_grouping_delete, form invalid : {form.errors!r}")

    return JsonResponse(data)


def axe_grouping_export_list(_):
    """
    Export Excel de la liste du Dictionnaire Axe Pro/Regroupement de facturation
    :return: response_file
    """
    try:

        today = pendulum.now()
        file_name = (
            f"LISTING_DES_AXE_PRO_VS_REGROUPEMENTS_DE_FACTURATION_"
            f"{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"
        )

        return response_file(excel_liste_axe_grouping, file_name, CONTENT_TYPE_EXCEL)

    except:
        LOGGER_VIEWS.exception("view : axe_grouping_export_list")

    return redirect(reverse("centers_purchasing:axe_grouping_list"))
