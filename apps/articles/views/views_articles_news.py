# pylint: disable=E0401,R0903,W0702,W0613
"""
Views des Nouveaux articles à valider ou changer
"""
import pendulum
from django.contrib import messages
from django.db import connection, transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from heron.loggers import LOGGER_EXPORT_EXCEL
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.core.functions.functions_http import get_pagination_buttons
from apps.edi.bin.edi_articles_news import SQL_FLAG_ERROR_SUB_CATEGORY
from apps.articles.excel_outputs.output_excel_articles_news_list import (
    excel_liste_articles_news,
)
from apps.articles.models import Article


# ECRANS DES NOUVEAUX ARTICLES =====================================================================
def new_articles_list(request):
    """Affichage de tous les nouveaux articles présents en base par pagination de 200"""
    limit = 200
    paginator = Paginator(
        Article.objects.filter(Q(new_article=True) | Q(error_sub_category=True)).values(
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
            "error_sub_category",
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
        "titre_table": f"1.1 - Liste des Nouveaux Articles",
        "url_validation": reverse("articles:articles_new_validation"),
        "url_redirect": reverse("articles:new_articles_list"),
    }
    return render(request, "articles/articles_news.html", context=context)


@transaction.atomic
def articles_new_validation(request):
    """Validation des nouveaux articles en masse"""

    nb_articles = (
        Article.objects.filter(Q(new_article=True) | Q(error_sub_category=True))
        .values(
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
            "error_sub_category",
        )
        .count()
    )

    if request.method == "POST" and nb_articles:
        with connection.cursor() as cursor:
            cursor.execute(SQL_FLAG_ERROR_SUB_CATEGORY)

        articles = Article.objects.filter(
            Q(axe_bu__isnull=False)
            & Q(axe_prj__isnull=False)
            & Q(axe_pro__isnull=False)
            & Q(axe_pys__isnull=False)
            & Q(axe_rfa__isnull=False)
            & Q(big_category__isnull=False)
            & Q(new_article=True)
            & Q(error_sub_category=False)
        )

        nb_updates = articles.update(new_article=False)
        level = 20

        if nb_articles == nb_updates:
            message = "Tous les articles ont étés mis à jour"

        else:
            level = 50
            message = "Il reste des articles qui comporte des erreus"

        messages.add_message(request, level, message)

    data = {"success": "ok"}
    return JsonResponse(data)


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
