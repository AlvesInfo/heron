# pylint: disable=E0401,R0903,W0702,W0613
"""
Views des Nouveaux articles à valider ou changer
"""
import pendulum
from django.shortcuts import render, redirect, reverse
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from heron.loggers import LOGGER_EXPORT_EXCEL
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.core.functions.functions_http import get_pagination_buttons

from apps.articles.excel_outputs.output_excel_articles_news_list import (
    excel_liste_articles_news,
)
from apps.articles.models import Article


# ECRANS DES NOUVEAUX ARTICLES =====================================================================
def new_articles_list(request):
    """Affichage de tous les nouveaux articles présents en base par pagination de 50"""
    limit = 200
    paginator = Paginator(
        Article.objects.filter(
            Q(axe_bu__isnull=True)
            | Q(axe_prj__isnull=True)
            | Q(axe_pro__isnull=True)
            | Q(axe_pys__isnull=True)
            | Q(axe_rfa__isnull=True)
            | Q(big_category__isnull=True)
            | Q(new_article=True)
        ).values(
            "pk",
            "third_party_num",
            "third_party_num__short_name",
            "reference",
            "libelle",
            "axe_bu__section",
            "axe_prj__section",
            "axe_pro__section",
            "axe_pys__section",
            "axe_rfa__section",
            "big_category__name",
            "sub_category__name",
        ),
        limit,
    )
    page = request.GET.get("page")

    try:
        articles = paginator.page(page)
    except PageNotAnInteger:
        articles = paginator.page(1)
    except EmptyPage:
        articles = paginator.page(paginator.num_pages)

    context = {
        "articles": articles,
        "pagination": get_pagination_buttons(
            articles.number, paginator.num_pages, nbre_boutons=5, position_color="darkgrey"
        ),
        "num_items": paginator.count,
        "num_pages": paginator.num_pages,
        "start_index": (articles.start_index() - 1) if articles.start_index() else 0,
        "end_index": articles.end_index(),
        "titre_table": f"1.1 - Liste des Nouveaux Articles"
    }
    return render(request, "articles/articles_news.html", context=context)


def articles_new_validation(request):
    """Validation des nouveaux articles"""
    context = {}
    return render(request, "articles/articles_news.html", context=context)


def articles_news_export_list(_):
    """
    Export Excel de la liste des Sociétés
    :param _: Request Django
    :return: response_file
    """
    try:

        today = pendulum.now()
        file_name = (
            f"LISTING_DES_NOUVEAUX_ARTICLES_{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"
        )

        return response_file(excel_liste_articles_news, file_name, CONTENT_TYPE_EXCEL)

    except:
        print('exception("view : articles_news_export_list")')
        LOGGER_EXPORT_EXCEL.exception("view : articles_news_export_list")

    return redirect(reverse("articles:new_articles_list"))
