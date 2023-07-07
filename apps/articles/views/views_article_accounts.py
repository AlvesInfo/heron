# pylint: disable=E0401,R0903,W0702,W0613
"""
Views des articles comptes comptables
"""
import pendulum
from django.shortcuts import redirect, reverse
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView, CreateView, UpdateView
from django.db.models import Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect, reverse

from heron.loggers import LOGGER_EXPORT_EXCEL
from apps.core.bin.change_traces import ChangeTraceMixin
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.core.functions.functions_http import get_pagination_buttons
from apps.articles.models import ArticleAccount
from apps.articles.parameters.querysets import articles_with_account_queryset


# ECRANS DES ARTICLES AVEC DES COMPTES =============================================================
def articles_account_list(request):
    """Affichage de tous les articles ayant des comptes comptables X3"""
    limit = 50

    paginator = Paginator(articles_with_account_queryset, limit)
    page = request.GET.get("page")

    try:
        articles = paginator.page(page)
    except PageNotAnInteger:
        articles = paginator.page(1)
    except EmptyPage:
        articles = paginator.page(paginator.num_pages)

    count = articles_with_account_queryset.count()
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
    }
    return render(request, "articles/articles_account.html", context=context)
