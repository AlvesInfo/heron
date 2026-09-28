# pylint: disable=E0401,R0903,W0702,W0613
"""
Views des articles comptes comptables
"""
import pendulum
from django.db import transaction
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.shortcuts import redirect, reverse
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView, CreateView, UpdateView
from django.db.models import Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect, reverse

from heron.loggers import LOGGER_EXPORT_EXCEL
from apps.core.bin.change_traces import ChangeTraceMixin, ACTION_DICT, get_difference_dict
from apps.core.models import ChangesTrace
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.core.functions.functions_http import get_pagination_buttons
from apps.articles.models import ArticleAccount
from apps.articles.forms import ArticleAccountUpdateForm
from apps.articles.filters import ArticleAccountFilter
from apps.articles.parameters.querysets import articles_with_account_queryset

# Centrale fille dont les comptes sont alignés sur ceux modifiés pour les autres centrales
CHILD_CENTER_MIRROR = "GAF"


# ECRANS DES ARTICLES AVEC DES COMPTES =============================================================
def articles_account_list(request):
    """Affichage de tous les articles ayant des comptes comptables X3"""
    limit = 50
    articles_filter = ArticleAccountFilter(request.GET, queryset=articles_with_account_queryset)
    attrs_filter = dict(articles_filter.data.items())
    paginator = Paginator(articles_filter.qs, limit)
    page = request.GET.get("page")

    try:
        articles = paginator.page(page)
    except PageNotAnInteger:
        articles = paginator.page(1)
    except EmptyPage:
        articles = paginator.page(paginator.num_pages)

    count = paginator.count
    titre_count = ""

    if count == 1:
        titre_count = " (1 article / comptes)"

    if count > 1:
        titre_count = f" ({str(count)} résultats)"

    context = {
        "articles": articles,
        "pagination": get_pagination_buttons(
            articles.number, paginator.num_pages, nbre_boutons=5, position_color="cadetblue"
        ),
        "num_items": paginator.count,
        "num_pages": paginator.num_pages,
        "start_index": (articles.start_index() - 1) if articles.start_index() else 0,
        "end_index": articles.end_index(),
        "titre_table": (
            f'12 - Articles / comptes <span style="font-size: .8em;">{titre_count}</span>'
        ),
        "url_validation": reverse("articles:articles_account_list"),
        "url_redirect": reverse("articles:articles_account_list"),
        "attrs_filter": attrs_filter,
        "form": articles_filter.form,
    }
    return render(request, "articles/articles_account.html", context=context)


class ArticleAccountUpdate(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """
    UpdateView de modification des comptes d'achat et de vente d'un article, pour une centrale
    et un code tva. C'est le seul endroit où un compte article existant peut être modifié,
    les recalculs automatiques ne font que créer les comptes manquants.
    """

    model = ArticleAccount
    form_class = ArticleAccountUpdateForm
    form_class.use_required_attribute = False
    template_name = "articles/articles_account_update.html"
    success_message = "Les comptes de l'article %(article)s ont été modifiés avec success"
    error_message = (
        "Les comptes de l'article %(article)s n'ont pu être modifiés, une erreur c'est produite"
    )

    def get_queryset(self):
        """Chargement en une requête des éléments affichés en lecture seule"""
        return super().get_queryset().select_related(
            "child_center", "vat", "article__third_party_num", "article__axe_pro",
            "article__big_category", "article__sub_category",
        )

    def get_list_url(self):
        """
        Url de retour : le paramètre next s'il est fourni (ex. fiche article), sinon la liste
        des articles / comptes, avec les filtres de recherche en cours
        """
        next_url = self.request.GET.get("next")

        if next_url and url_has_allowed_host_and_scheme(
            next_url, allowed_hosts={self.request.get_host()}
        ):
            return next_url

        url = reverse("articles:articles_account_list")
        query_dict = self.request.GET.copy()
        query_dict.pop("next", None)
        query_string = query_dict.urlencode()
        return f"{url}?{query_string}" if query_string else url

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["chevron_retour"] = self.get_list_url()
        context["titre_table"] = f"Modification des comptes de l'article {self.object.article}"
        return context

    def update_mirror_account(self, cleaned_data):
        """
        Aligne les comptes de la centrale fille CHILD_CENTER_MIRROR, pour le même article
        et le même code tva, sur les comptes saisis. La ligne est créée si elle n'existe pas.
        :param cleaned_data: données validées du formulaire
        :return: message à ajouter au message de succès
        """
        if self.object.child_center_id == CHILD_CENTER_MIRROR:
            return ""

        update_dict = {
            "purchase_account": cleaned_data.get("purchase_account"),
            "sale_account": cleaned_data.get("sale_account"),
        }
        mirror = ArticleAccount.objects.filter(
            article=self.object.article_id,
            vat=self.object.vat_id,
            child_center=CHILD_CENTER_MIRROR,
        ).first()

        if mirror is None:
            before = {}
            mirror = ArticleAccount.objects.create(
                article_id=self.object.article_id,
                vat_id=self.object.vat_id,
                child_center_id=CHILD_CENTER_MIRROR,
                **update_dict,
            )
            action_type = "CREATE"
            message = f", compte {CHILD_CENTER_MIRROR} créé avec les mêmes comptes"

        else:
            if all(getattr(mirror, key) == value for key, value in update_dict.items()):
                return f", comptes {CHILD_CENTER_MIRROR} déjà identiques"

            before = {key: value for key, value in mirror.__dict__.items() if key != "_state"}

            for key, value in update_dict.items():
                setattr(mirror, key, value)

            mirror.save()
            action_type = "UPDATE"
            message = f", ainsi que pour la centrale {CHILD_CENTER_MIRROR}"

        after = {key: value for key, value in mirror.__dict__.items() if key != "_state"}

        ChangesTrace.objects.create(
            action_datetime=timezone.now(),
            action_type=ACTION_DICT.get(action_type),
            function_name=self.__class__,
            action_by=self.request.user,
            before=before,
            after=after,
            difference=get_difference_dict(before, after),
            model_name=ArticleAccount._meta.model_name,
            model=ArticleAccount._meta.model,
            db_table=ArticleAccount._meta.db_table,
        )

        return message

    def form_valid(self, form):
        """La ligne modifiée et celle de la centrale miroir sont mises à jour ensemble"""
        with transaction.atomic():
            self.mirror_message = self.update_mirror_account(form.cleaned_data)
            return super().form_valid(form)

    def get_success_message(self, cleaned_data):
        """Message avec l'article, la centrale et la tva modifiés"""
        return self.success_message % {
            "article": (
                f"{self.object.article} - centrale {self.object.child_center_id} "
                f"- tva {self.object.vat_id}"
            )
        } + getattr(self, "mirror_message", "")

    def get_success_url(self):
        """Retour à la liste des articles / comptes, sur la recherche en cours"""
        return self.get_list_url()
