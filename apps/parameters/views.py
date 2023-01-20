# pylint: disable=E0401,R0903,W0702,W0613,R0901,E1101,W0201
"""
Views des Paramètres
"""
import pendulum
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, reverse
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView, CreateView, UpdateView

from heron.loggers import LOGGER_VIEWS
from apps.core.bin.change_traces import ChangeTraceMixin
from apps.core.bin.change_traces import trace_mark_delete
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.parameters.excel_outputs.parameters_excel_categories_list import (
    excel_liste_categories,
)
from apps.parameters.excel_outputs.parameters_excel_axe_articles_defaut_list import (
    excel_list_axe_article_defaut,
)
from apps.parameters.models import Category, SubCategory, DefaultAxeArticle
from apps.parameters.forms import (
    CategoryForm,
    SubCategoryForm,
    DeleteSubCategoryForm,
    DefaultAxeArticleForm,
)


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
        context["titre_table"] = "Mise à jour Catégorie"
        context["chevron_retour"] = reverse("parameters:categories_list")
        return super().get_context_data(**context)

    @transaction.atomic
    def form_valid(self, form):
        form.instance.modified_by = self.request.user
        self.request.session["level"] = 20
        return super().form_valid(form)

    def form_invalid(self, form):
        self.request.session["level"] = 50
        return super().form_invalid(form)


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


# ECRANS DES RUBRIQUES PRESTA ======================================================================


class SubCategoryCreate(ChangeTraceMixin, SuccessMessageMixin, CreateView):
    """CreateView de création des Catégories"""

    model = SubCategory
    form_class = SubCategoryForm
    form_class.use_required_attribute = False
    template_name = "parameters/sub_category_update.html"
    success_message = "La Rubrique Presta %(name)s a été créé avec success"
    error_message = "La Rubrique Presta %(name)s n'a pu être créé, une erreur c'est produite"

    def get(self, request, *args, **kwargs):
        """Ajout de self.category a l'instance de la vue"""
        try:
            self.category = Category.objects.get(pk=kwargs.get("category_pk"))
        except Category.DoesNotExist:
            pass
        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        """Ajout de self.category a l'instance de la vue"""
        self.object = None
        try:
            self.category = Category.objects.get(pk=kwargs.get("category_pk"))
        except Category.DoesNotExist:
            pass
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["create"] = True
        context["chevron_retour"] = reverse(
            "parameters:category_update", kwargs={"pk": self.category.pk}
        )
        context["titre_table"] = f"Création Rubrique de Prestation : {self.category}"
        context["category"] = self.category
        context["category_new"] = self.category.big_sub_category.all().count() + 1
        return context

    def get_success_url(self):
        """Surcharge de l'url en case de succes pour revenir à la catégorie où l'on était"""

        return reverse("parameters:category_update", kwargs={"pk": self.category.pk})


class SubCategoryUpdate(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView pour modification des identifiants pour les fournisseurs EDI"""

    model = SubCategory
    form_class = SubCategoryForm
    form_class.use_required_attribute = False
    template_name = "parameters/sub_category_update.html"
    success_message = "La Rubrique Presta %(name)s a été modifiée avec success"
    error_message = "La Rubrique Presta %(name)s n'a pu être modifiée, une erreur c'est produite"

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["create"] = True
        context["chevron_retour"] = reverse(
            "parameters:category_update", kwargs={"pk": self.object.big_category.pk}
        )
        context["titre_table"] = "Modification de la Rubrique de Prestation"
        context["category_new"] = self.object.ranking
        context["category"] = self.object.big_category
        return context

    def get_success_url(self):
        """Surcharge de l'url en case de succes pour revenir à la catégorie où l'on était"""

        return reverse("parameters:category_update", kwargs={"pk": self.object.big_category.pk})


@transaction.atomic
def delete_sub_category(request):
    """Suppression des rubriques prestas
    :param request: Request Django
    :return: view
    """

    if not request.is_ajax() and request.method != "POST":
        return redirect("home")

    data = {"success": "ko"}
    id_pk = request.POST.get("pk")
    form = DeleteSubCategoryForm({"id": id_pk})

    if form.is_valid():
        trace_mark_delete(
            request=request,
            django_model=SubCategory,
            data_dict={"id": id_pk},
            force_delete=True,
        )
        data = {"success": "success"}

    else:
        print(form.errors)
        LOGGER_VIEWS.exception(f"delete_invoice_purchase, form invalid : {form.errors!r}")

    return JsonResponse(data)


# ECRANS DES AXES SUR LES ARTICLES PAR DEFAUT ======================================================


class DefaultAxeAricleUpdate(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView pour modification Axes et catégorie par défaut des articles"""
    model = DefaultAxeArticle
    form_class = DefaultAxeArticleForm
    form_class.use_required_attribute = False
    slug_field = "slug_name"
    slug_url_kwarg = "slug_name"
    template_name = "parameters/axes_articles_defaut_update.html"
    success_message = "Les catégories et axes ont été modifiés avec success"
    error_message = "Les catégories et axes  n'ont pu être modifiés, une erreur c'est produite"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titre_table"] = "Catégories et Axes par défaut pour les articles"
        context["chevron_retour"] = reverse("home")
        return context

    def form_valid(self, form):
        form.instance.modified_by = self.request.user
        self.request.session["level"] = 20
        return super().form_valid(form)

    def form_invalid(self, form):
        self.request.session["level"] = 50
        return super().form_invalid(form)


def axe_articles_defaut_export_list(_):
    """
    Export Excel de la liste des Axes par défaut pour les articles
    :return: response_file axes_articles
    """
    try:

        today = pendulum.now()
        file_name = (
            f"LISTING_DES_AXES_ARTICLES_PAR_DEFAUT_"
            f"{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"
        )

        return response_file(excel_list_axe_article_defaut, file_name, CONTENT_TYPE_EXCEL)

    except:
        LOGGER_VIEWS.exception("view : export_list_societies")

    return redirect(reverse("book:societies_list"))
