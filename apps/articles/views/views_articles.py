# pylint: disable=E0401,R0903,W0702,W0613
"""
Views des Paramètres
"""
import pendulum
from django.shortcuts import redirect, reverse
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView, CreateView, UpdateView
from django.db import transaction
from django.db.models import Count

from heron.loggers import LOGGER_VIEWS
from apps.core.bin.change_traces import ChangeTraceMixin
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL

from apps.articles.excel_outputs.output_excel_articles_list import (
    excel_liste_articles,
)
from apps.book.models import Society
from apps.articles.models import Article
from apps.articles.forms import ArticleForm


# ECRANS DES ARTICLES ============================================================================
class SuppliersArticlesList(ListView):
    """View de la liste des Fournisseurs ayant des Articles dans la base"""

    model = Society
    context_object_name = "suppliers"
    queryset = Society.objects.filter(
        third_party_num__in=Article.objects.values("third_party_num")
        .annotate(nb_plan=Count("third_party_num"))
        .order_by("third_party_num")
        .values_list("third_party_num", flat=True)
    )
    template_name = "articles/suppliers_articles_list.html"
    extra_context = {"titre_table": "Fournisseurs - Articles"}


class ArticlesList(ListView):
    """View de la liste des Catégories"""

    model = Article
    context_object_name = "articles"
    template_name = "articles/articles_list.html"

    def get_queryset(self, **kwargs):
        self.third_party_num = self.kwargs.get("third_party_num", "")
        queryset = Article.objects.filter(third_party_num=self.third_party_num)
        return queryset

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["chevron_retour"] = reverse("articles:suppliers_articles_list")
        context["titre_table"] = f"Articles Marchandises du Tiers {self.third_party_num}"
        context["third_party_num"] = self.third_party_num
        return context


class ArticleCreate(ChangeTraceMixin, SuccessMessageMixin, CreateView):
    """CreateView de création des Categories"""

    model = Article
    form_class = ArticleForm
    form_class.use_required_attribute = False
    template_name = "articles/article_update.html"
    success_message = "L'Article %(reference)s a été créé avec success"
    error_message = "L'Article %(reference)s n'a pu être créé, une erreur c'est produite"

    def get(self, request, *args, **kwargs):
        """Handle GET requests: instantiate a blank version of the form."""
        third_party_num = self.kwargs.get("third_party_num", "")
        if third_party_num == "create":
            self.third_party_num = None
            self.base_create = True
        else:
            self.base_create = False
            self.third_party_num = Society.objects.get(third_party_num=third_party_num)
        self.object = None
        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        """Rajout de third_party_num dans le post"""
        third_party_num = self.kwargs.get("third_party_num", "")
        if third_party_num == "create":
            self.third_party_num = None
            self.base_create = True
        else:
            self.base_create = False
            self.third_party_num = Society.objects.get(third_party_num=third_party_num)
        self.object = None
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["article"] = "Article :"
        context["base_create"] = self.base_create

        if not self.base_create:
            context[
                "titre_table"
            ] = f"Création d'un Nouvel Article pour le Tiers : {self.third_party_num.third_party_num}"
            context["chevron_retour"] = reverse(
                "articles:articles_list",
                args=[
                    self.third_party_num.third_party_num,
                ],
            )
            context["third_party_num"] = self.third_party_num.third_party_num
        else:
            context["chevron_retour"] = reverse("articles:suppliers_articles_list")

        return context

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        return reverse(
            "articles:articles_list",
            args=[
                self.object.third_party_num.third_party_num,
            ],
        )

    @transaction.atomic
    def form_valid(self, form):
        form.instance.modified_by = self.request.user
        if not form.instance.libelle_heron:
            form.instance.libelle_heron = form.instance.libelle
        self.request.session["level"] = 20
        return super().form_valid(form)

    def form_invalid(self, form):
        self.request.session["level"] = 50
        return super().form_invalid(form)


class ArticleUpdate(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView pour modification des identifiants pour les fournisseurs EDI"""

    model = Article
    form_class = ArticleForm
    form_class.use_required_attribute = False
    pk_url_kwarg = "pk"
    template_name = "articles/article_update.html"
    success_message = "L'Article %(reference)s a été modifié avec success"
    error_message = "L'Article %(reference)s n'a pu être modifié, une erreur c'est produite"

    def get(self, request, *args, **kwargs):
        """Handle GET requests: instantiate a blank version of the form."""
        self.third_party_num = self.kwargs.get("third_party_num", "")
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["chevron_retour"] = reverse(
            "articles:articles_list", args=[self.object.third_party_num.third_party_num]
        )
        context["titre_table"] = f"Mise à jour Article {str(self.object)}"
        context["article"] = f"Article Référence : {self.object.reference}"
        context["third_party_num"] = self.object.third_party_num.third_party_num
        return context

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        return reverse(
            "articles:articles_list",
            args=[
                self.object.third_party_num.third_party_num,
            ],
        )

    @transaction.atomic
    def form_valid(self, form):
        """Si le formulaire est valide"""
        form.instance.modified_by = self.request.user
        self.request.session["level"] = 20
        return super().form_valid(form)

    def form_invalid(self, form):
        """On élève le niveau d'alerte en cas de formulaire invalide"""
        self.request.session["level"] = 50
        return super().form_invalid(form)


def articles_export_list(_, third_party_num):
    """
    Export Excel de la liste des Sociétés
    :param _: Request Django
    :param third_party_num: N° de tiers X3
    :return: response_file
    """
    try:

        today = pendulum.now()
        file_name = f"LISTING_DES_ARTICLES_{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"

        return response_file(excel_liste_articles, file_name, CONTENT_TYPE_EXCEL, third_party_num)

    except:
        LOGGER_VIEWS.exception("view : articles_export_list")

    return redirect(reverse("articles:articles_list", {"third_party_num": third_party_num}))
