# pylint: disable=E0401,R0903,W0702,W0613,W0201
"""
Views des Articles
"""
import pendulum
from django.shortcuts import redirect, reverse
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView, CreateView, UpdateView
from django.db.models import Count, F
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render

from heron.loggers import LOGGER_EXPORT_EXCEL
from apps.core.bin.change_traces import ChangeTraceMixin
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.core.functions.functions_http import get_pagination_buttons
from apps.articles.excel_outputs.output_excel_articles_list import (
    excel_liste_articles,
)
from apps.articles.bin.sub_category import check_sub_category
from apps.book.models import Society
from apps.parameters.models import Category
from apps.articles.models import Article
from apps.articles.forms import ArticleForm, ArticleSearchForm
from apps.edi.models import EdiImport
from apps.centers_purchasing.bin.update_account_article import set_update_articles_account
from apps.articles.filters import ArticleFilter


# ECRANS DES ARTICLES ============================================================================
class SuppliersArticlesList(ListView):
    """View de la liste des Fournisseurs ayant des Articles dans la base"""

    model = Society
    context_object_name = "suppliers"
    template_name = "articles/suppliers_articles_list.html"
    extra_context = {}

    def get(self, request, *args, **kwargs):
        """add context in get request"""
        self.extra_context.update(kwargs)
        categorie = Category.objects.get(slug_name=self.kwargs.get("category")).name
        self.extra_context["titre_table"] = f"Articles : {categorie}"
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Return the list of items for this view.
        The return value must be an iterable and may be an instance of
        `QuerySet` in which case `QuerySet` specific behavior will be enabled.
        """
        queryset = (
            Article.objects.filter(big_category__slug_name=self.kwargs.get("category"))
            .values("third_party_num", "third_party_num__name")
            .annotate(nb_articles=Count("third_party_num"))
            .order_by("third_party_num")
        )
        ordering = self.get_ordering()

        if ordering:
            if isinstance(ordering, str):
                ordering = (ordering,)
            queryset = queryset.order_by(*ordering)

        return queryset


class ArticlesList(ListView):
    """View de la liste des Articles"""

    model = Article
    context_object_name = "articles"
    template_name = "articles/articles_list.html"
    extra_context = {}

    def get(self, request, *args, **kwargs):
        """add context in get request"""
        self.extra_context.update(kwargs)
        self.third_party_num = self.extra_context.get("third_party_num")
        self.category = Category.objects.get(slug_name=self.extra_context.get("category"))
        self.extra_context[
            "titre_table"
        ] = f"Articles : {self.category.name} du Tiers {self.third_party_num}"
        self.extra_context["chevron_retour"] = reverse(
            "articles:suppliers_articles_list", args=(self.category.slug_name,)
        )
        return super().get(request, *args, **kwargs)

    def get_queryset(self, **kwargs):
        """Change queryset in context"""
        queryset = (
            Article.objects.filter(
                third_party_num=self.third_party_num,
                big_category__slug_name=self.category.slug_name,
            )
            .values(
                "pk",
                "reference",
                "libelle",
                "libelle_heron",
                "axe_pro__section",
                "axe_bu__section",
                "axe_prj__section",
                "axe_pys__section",
                "axe_rfa__section",
                "comment",
            )
            .order_by("-created_at", "reference")[:1000]
        )

        return queryset


class ArticleCreate(ChangeTraceMixin, SuccessMessageMixin, CreateView):
    """CreateView de création d'Articles"""

    model = Article
    form_class = ArticleForm
    form_class.use_required_attribute = False
    template_name = "articles/article_update.html"
    success_message = "L'Article %(reference)s a été créé avec success"
    error_message = "L'Article %(reference)s n'a pu être créé, une erreur c'est produite"

    def get(self, request, *args, **kwargs):
        """Handle GET requests: instantiate a blank version of the form."""
        self.third_party_num = self.kwargs.get("third_party_num", "")
        self.category = self.kwargs.get("category", "")

        if self.third_party_num == "create":
            self.third_party_num = None
            self.base_create = True
        else:
            self.base_create = False
            self.third_party_num = Society.objects.get(third_party_num=self.third_party_num)

        self.object = None
        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        """Rajout de third_party_num dans le post"""
        self.third_party_num = self.kwargs.get("third_party_num", "")
        self.category = self.kwargs.get("category", "")

        if self.third_party_num == "create":
            self.third_party_num = None
            self.base_create = True
        else:
            self.base_create = False
            self.third_party_num = Society.objects.get(third_party_num=self.third_party_num)
        self.object = None
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["article"] = "Article :"
        context["base_create"] = self.base_create

        if not self.base_create:
            context["titre_table"] = (
                "Création d'un Nouvel Article pour le Tiers : "
                f"{self.third_party_num.third_party_num}"
            )
            context["chevron_retour"] = reverse(
                "articles:articles_list",
                args=(
                    self.third_party_num.third_party_num,
                    self.category,
                ),
            )
            context["third_party_num"] = self.third_party_num.third_party_num
        else:
            context["chevron_retour"] = reverse(
                "articles:suppliers_articles_list", args=(self.category,)
            )

        return context

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        return reverse(
            "articles:articles_list",
            args=[
                self.object.third_party_num.third_party_num,
                self.category,
            ],
        )

    def form_valid(self, form):
        """Ajout de l'user à la sauvegarde du formulaire"""
        form.instance.created_by = self.request.user
        self.request.session["level"] = 20

        # On vérifie la cohérence entre catégory et sous-catégorie
        if form.instance.sub_category and not check_sub_category(
            form.instance.sub_category.uuid_identification,
            form.instance.big_category.uuid_identification,
        ):
            form.instance.sub_category = None

        return super().form_valid(form)

    def form_updated(self):
        """Action à faire après form_valid save"""

        # On met à jour les articles des edi table edi_ediimport
        third_party_num = self.object.third_party_num.third_party_num
        reference = self.object.reference
        EdiImport.objects.filter(
            third_party_num=third_party_num, reference_article=reference
        ).update(
            axe_bu=self.object.axe_bu,
            axe_prj=self.object.axe_prj,
            axe_pro=self.object.axe_pro,
            axe_pys=self.object.axe_pys,
            axe_rfa=self.object.axe_rfa,
            big_category=self.object.big_category,
            sub_category=self.object.sub_category,
        )

        # On met à jour les comptes comptable des articles
        set_update_articles_account(article_uuid=self.object.uuid_identification)


class ArticleUpdate(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView pour modification des Articles"""

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
            "articles:articles_list",
            args=(
                self.object.third_party_num.third_party_num,
                self.object.big_category.slug_name,
            ),
        )
        context["titre_table"] = f"Mise à jour Article {str(self.object)}"
        context["article"] = f"Article Référence : {self.object.reference}"
        context["third_party_num"] = self.object.third_party_num.third_party_num
        return context

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        return reverse(
            "articles:articles_list",
            args=(
                self.object.third_party_num.third_party_num,
                self.object.big_category.slug_name,
            ),
        )

    def form_valid(self, form, **kwargs):
        """Ajout de l'user à la sauvegarde du formulaire"""
        form.instance.modified_by = self.request.user
        self.request.session["level"] = 20

        # On vérifie la cohérence entre catégory et sous-catégorie
        if form.instance.sub_category and not check_sub_category(
            form.instance.sub_category.uuid_identification,
            form.instance.big_category.uuid_identification,
        ):
            form.instance.sub_category = None

        return super().form_valid(form)

    def form_updated(self):
        """Action à faire après form_valid save"""

        # On met à jour les articles des edi table edi_ediimport
        third_party_num = self.object.third_party_num.third_party_num
        reference = self.object.reference
        EdiImport.objects.filter(
            third_party_num=third_party_num, reference_article=reference
        ).update(
            axe_bu=self.object.axe_bu,
            axe_prj=self.object.axe_prj,
            axe_pro=self.object.axe_pro,
            axe_pys=self.object.axe_pys,
            axe_rfa=self.object.axe_rfa,
            big_category=self.object.big_category,
            sub_category=self.object.sub_category,
        )

        # On met à jour les comptes comptable des articles
        set_update_articles_account(article_uuid=self.object.uuid_identification)


def articles_search_list(request):
    """Affichage de la page de recherche des articles"""
    limit = 50
    queryset = (
        Article.objects.annotate(
            big_category_n=F("big_category__name"),
            sub_category_n=F("sub_category__name"),
            pk=F("id"),
        )
        .values(
            "pk",
            "third_party_num",
            "third_party_num__name",
            "reference",
            "libelle",
            "libelle_heron",
            "big_category_n",
            "sub_category_n",
            "axe_pro__section",
        )
        .order_by(
            "third_party_num", "reference", "big_category_n", "sub_category_n", "axe_pro__section"
        )
    )
    articles_filter = ArticleFilter(request.GET, queryset=queryset)
    attrs_filter = dict(articles_filter.data.items())
    paginator = Paginator(articles_filter.qs, limit)
    page = request.GET.get("page")
    form = ArticleSearchForm(attrs_filter)

    try:
        articles = paginator.page(page)
    except PageNotAnInteger:
        articles = paginator.page(1)
    except EmptyPage:
        articles = paginator.page(paginator.num_pages)

    count = articles_filter.qs.count()
    titre_count = ""

    if count == 1:
        titre_count = " (1 article trouvé)"

    if count > 1:
        titre_count = f" ({str(count)} articles trouvés)"

    context = {
        "articles": paginator.get_page(page),
        "filter": articles_filter,
        "pagination": get_pagination_buttons(
            articles.number, paginator.num_pages, nbre_boutons=5, position_color="cadetblue"
        ),
        "num_items": paginator.count,
        "num_pages": paginator.num_pages,
        "start_index": (articles.start_index() - 1) if articles.start_index() else 0,
        "end_index": articles.end_index(),
        "titre_table": f'11. Recherche Articles<span style="font-size: .8em;">{titre_count}</span>',
        "url_redirect": reverse("articles:articles_search_list"),
        "attrs_filter": attrs_filter,
        "form": form,
    }
    return render(request, "articles/articles_search.html", context=context)


def articles_export_list(_, third_party_num, category):
    """
    Export Excel de la liste des Articles par Fournisseurs et Catégories
    :param _: Request Django
    :param third_party_num: N° de tiers X3
    :param category: slug_name de la catégorie
    :return: response_file
    """
    try:
        today = pendulum.now()
        file_name = f"LISTING_DES_ARTICLES_{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"

        return response_file(
            excel_liste_articles, file_name, CONTENT_TYPE_EXCEL, third_party_num, category
        )

    except:
        LOGGER_EXPORT_EXCEL.exception("view : articles_export_list")

    return redirect(
        reverse(
            "articles:articles_list", {"third_party_num": third_party_num, "category": category}
        )
    )
