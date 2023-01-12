# pylint: disable=E0401,R0903,W0702,W0613
"""
Views des Paramètres
"""
import pendulum
from django.db import transaction
from django.shortcuts import redirect, reverse
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView, CreateView, UpdateView

from heron.loggers import LOGGER_VIEWS
from apps.core.bin.change_traces import ChangeTraceMixin, trace_form_change
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.parameters.excel_outputs.parameters_excel_categories_list import (
    excel_liste_categories,
)
from apps.parameters.models import Category, SubCategory
from apps.parameters.forms import CategoryForm, SubCategoryForm, InlineCategoryFormmset


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
        """Insert the form into the context dict."""

        context = super().get_context_data(**kwargs)

        if self.request.POST:
            context["sub_category_formset"] = InlineCategoryFormmset(
                self.request.POST,
                instance=self.object,
                prefix="big_sub_category",
            )
            context["sub_category_formset"].clean()
        else:
            context["sub_category_formset"] = InlineCategoryFormmset(
                instance=self.object, prefix="big_sub_category"
            )

        return super().get_context_data(**context)

    @transaction.atomic
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context.get("sub_category_formset")
        with transaction.atomic():
            form.instance.created_by = self.request.user
            self.object = form.save()
            if formset.is_valid():
                formset.instance = self.object
                for form_s in formset:
                    print(form_s.is_valid())
                    if form_s.changed_data:
                        print(form_s.changed_data)
                        if "DELETE" in form_s.changed_data:
                            print("DELETE : ", form_s.changed_data)
                            print(dir(form_s))
                            form_s.save()

        form.instance.modified_by = self.request.user
        self.request.session["level"] = 20
        return super().form_valid(form)

    def form_invalid(self, form):
        self.request.session["level"] = 50
        return super().form_invalid(form)


class SubCategoryUpdate(SuccessMessageMixin, UpdateView):
    """UpdateView pour modification des identifiants pour les fournisseurs EDI"""

    model = SubCategory
    form_class = SubCategoryForm
    form_class.use_required_attribute = False
    template_name = "parameters/category_update.html"
    success_message = "Les Rubriques Presta ont été modifiées avec success"
    error_message = "Les Rubriques Presta n'ont pu être modifiées, une erreur c'est produite"


def categories_export_list(_):
    """
    Export Excel de la liste des Sociétés
    :param _: Request Django
    :return: response_file
    """
    try:

        today = pendulum.now()
        file_name = f"LISTING_DES_CATEGORIES_{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"

        return response_file(excel_liste_categories, file_name, CONTENT_TYPE_EXCEL)

    except:
        LOGGER_VIEWS.exception("view : categories_export_list")

    return redirect(reverse("parameters:categories_list"))
