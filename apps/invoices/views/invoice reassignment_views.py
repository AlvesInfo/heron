# pylint: disable=E0401
"""
Views pour réafecter sur une facture, précédente, soit un mauvais code de la part du fournisseur,
ou une mauvaise affectation de l'opérateur qui a effectué la facturationion précédente.

Commentaire:

created at: 2023-07-07
created by: Paulo ALVES

modified at: 2023-07-07
modified by: Paulo ALVES
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


def invoice_search_list(request):
    """Affichage de la page de recherche des Factures pour la réaffectation"""
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
