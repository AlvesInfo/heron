# pylint: disable=E0401,R0903,W0702,W0613
"""
Views des Paramètres
"""
import pendulum
from django.shortcuts import redirect, reverse
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView, CreateView, UpdateView

from heron.loggers import ERROR_VIEWS_LOGGER
from apps.core.bin.change_traces import ChangeTraceMixin
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.parameters.excel_outputs.parameters_excel_categories_list import (
    excel_liste_categories,
)
from apps.parameters.models import Category
from apps.parameters.forms import CategoryForm


# ECRANS DES CATEGORIES ============================================================================
class CategoriesList(ListView):
    """View de la liste des Catégories"""

    model = Category
    context_object_name = "categories"
    template_name = "parameters/categories_list.html"
    extra_context = {"titre_table": "Catégories"}


class CategoryCreate(ChangeTraceMixin, SuccessMessageMixin, CreateView):
    """CreateView de création des Catégories"""

    model = Category
    form_class = CategoryForm
    form_class.use_required_attribute = False
    template_name = "parameters/category_update.html"
    success_message = "La Catégorie %(name)s a été créé avec success"
    error_message = "La Catégorie %(name)s n'a pu être créé, une erreur c'est produite"

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["create"] = True
        context["chevron_retour"] = reverse("parameters:categories_list")
        context["titre_table"] = "Création d'une nouvelle Catégorie"
        return context


class CategoryUpdate(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView pour modification des identifiants pour les fournisseurs EDI"""

    model = Category
    form_class = CategoryForm
    form_class.use_required_attribute = False
    template_name = "parameters/category_update.html"
    success_message = "La Catégorie %(name)s a été modifiée avec success"
    error_message = "La Catégorie %(name)s n'a pu être modifiée, une erreur c'est produite"

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["chevron_retour"] = reverse("parameters:categories_list")
        context["titre_table"] = (
            f"Mise à jour de la Catégorie : "
            f"{context.get('object').ranking} - "
            f"{context.get('object').name}"
        )
        return context


def categories_export_list(request):
    """
    Export Excel de la liste des Sociétés
    :param request: Request Django
    :return: response_file
    """
    try:

        today = pendulum.now()
        file_name = f"LISTING_DES_CATEGORIES_{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"

        return response_file(excel_liste_categories, file_name, CONTENT_TYPE_EXCEL)

    except:
        ERROR_VIEWS_LOGGER.exception("view : categories_export_list")

    return redirect(reverse("parameters:categories_list"))
