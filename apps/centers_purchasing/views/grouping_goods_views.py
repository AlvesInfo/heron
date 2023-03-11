# pylint: disable=E0401,R0903
"""
FR : Module des regroupements de facturation
     dito onglets 2. et 2.1 du fichier bloc de facturation transmis aux maisons
EN : Billing groups module
     ditto tabs 2. and 2.1 of the invoicing block file transmitted to the houses

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
from apps.centers_purchasing.excel_outputs.output_excel_grouping_goods_list import (
    excel_liste_grouping_goods,
)
from apps.centers_purchasing.models import GroupingGoods
from apps.centers_purchasing.forms import (
    GroupingGoodsForm,
    GroupingGoodsDeleteForm,
)

# Regroupement factures


class GroupingGoodsList(ListView):
    """View de la liste des Regroupements de facturation"""

    model = GroupingGoods
    context_object_name = "grouping_goods"
    template_name = "centers_purchasing/grouping_goods_list.html"
    extra_context = {"titre_table": "Regroupements de facturation"}


class GroupingGoodsCreate(ChangeTraceMixin, SuccessMessageMixin, CreateView):
    """CreateView de création de la liste des Regroupements de facturation"""

    model = GroupingGoods
    form_class = GroupingGoodsForm
    form_class.use_required_attribute = False
    template_name = "centers_purchasing/grouping_goods_update.html"
    success_message = "Le regroupement de facturation a été créé avec success"
    error_message = "Le regroupement de facturation n'a pu être créé, une erreur c'est produite"

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["chevron_retour"] = reverse("centers_purchasing:grouping_goods_list")
        context["titre_table"] = "Création d'un nouveau regroupement de facturation"
        context["create"] = True
        context["ranking"] = max([0, *[row.ranking for row in GroupingGoods.objects.all()]]) + 1
        return context

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        return reverse("centers_purchasing:grouping_goods_list")

    def form_valid(self, form):
        """Ajout de l'user à la sauvegarde du formulaire"""
        form.instance.created_by = self.request.user
        self.request.session["level"] = 20
        return super().form_valid(form)


class GroupingGoodsUpdate(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView d'update de la liste des Regroupements de facturation"""

    model = GroupingGoods
    form_class = GroupingGoodsForm
    form_class.use_required_attribute = False
    template_name = "centers_purchasing/grouping_goods_update.html"
    success_message = "Le regroupement de facturation a été modifié avec success"
    error_message = "Le regroupement de facturation n'a pu être modifié, une erreur c'est produite"

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["chevron_retour"] = reverse("centers_purchasing:grouping_goods_list")
        context["titre_table"] = "Mise à jour d'un regroupement de facturation"
        context["ranking"] = self.object.ranking
        return context

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        return reverse("centers_purchasing:grouping_goods_list")

    def form_valid(self, form, **kwargs):
        """Ajout de l'user à la sauvegarde du formulaire"""
        form.instance.modified_by = self.request.user
        self.request.session["level"] = 20
        return super().form_valid(form)


def grouping_goods_delete(request):
    """Vue ajax de suppresion d'une ligne de la table"""

    if not request.is_ajax() and request.method != "POST":
        return redirect("home")

    data = {"success": "ko"}
    id_pk = request.POST.get("pk")
    form = GroupingGoodsDeleteForm({"id": id_pk})

    if form.is_valid():
        trace_mark_delete(
            request=request,
            django_model=GroupingGoods,
            data_dict={"id": id_pk},
            force_delete=True,
        )
        data = {"success": "success"}

    else:
        LOGGER_VIEWS.exception(f"grouping_goods_delete, form invalid : {form.errors!r}")

    return JsonResponse(data)


def grouping_goods_export_list(_):
    """
    Export Excel de la liste des Regroupements de facturation
    :return: response_file
    """
    try:

        today = pendulum.now()
        file_name = (
            f"LISTING_DES_REGROUPEMENTS_DE_FACTURATION_"
            f"{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"
        )

        return response_file(excel_liste_grouping_goods, file_name, CONTENT_TYPE_EXCEL)

    except:
        LOGGER_VIEWS.exception("view : grouping_goods_export_list")

    return redirect(reverse("centers_purchasing:grouping_goods_list"))
