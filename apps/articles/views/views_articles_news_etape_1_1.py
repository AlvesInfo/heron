# pylint: disable=E0401,R0903,W0702,W0613,W0212
"""
Views des Nouveaux articles à valider ou changer
"""
import inspect

import pendulum
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import connection, transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, reverse
from django.utils import timezone

from heron.loggers import LOGGER_EXPORT_EXCEL
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.core.functions.functions_http import get_pagination_buttons
from apps.core.models import ChangesTrace
from apps.edi.bin.edi_articles_news import (
    insert_new_articles,
    SQL_FLAG_ERROR_SUB_CATEGORY,
    SQL_FLAG_WITHOUT_AXES,
    SQL_EDI_IMPORT_ARTICLES,
    SQL_AXE_BU,
    SQL_AXE_PRJ,
    SQL_AXE_PRO,
    SQL_AXE_PYS,
    SQL_AXE_RFA,
)
from apps.articles.excel_outputs.output_excel_articles_news_list import (
    excel_liste_articles_news,
)
from apps.articles.models import Article
from apps.centers_purchasing.bin.update_account_article import set_update_articles_confict_account


# ECRANS DES NOUVEAUX ARTICLES =====================================================================
def new_articles_list(request):
    """Affichage de tous les nouveaux articles présents en base par pagination de 200"""
    limit = 200

    # On met à jour les articles sans axes ou en erreur de rubrique presta avant affichage
    with connection.cursor() as cursor:
        insert_new_articles(cursor)
        cursor.execute(SQL_FLAG_ERROR_SUB_CATEGORY)
        cursor.execute(SQL_FLAG_WITHOUT_AXES)
        cursor.execute(SQL_AXE_BU)
        cursor.execute(SQL_AXE_PRJ)
        cursor.execute(SQL_AXE_PRO)
        cursor.execute(SQL_AXE_PYS)
        cursor.execute(SQL_AXE_RFA)

    paginator = Paginator(
        Article.objects.filter(
            Q(new_article=True)
            | Q(error_sub_category=True)
            | Q(axe_bu__isnull=True)
            | Q(axe_prj__isnull=True)
            | Q(axe_pro__isnull=True)
            | Q(axe_pys__isnull=True)
            | Q(axe_rfa__isnull=True)
            | Q(big_category__isnull=True)
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
            articles.number, paginator.num_pages, nbre_boutons=5, position_color="cadetblue"
        ),
        "num_items": paginator.count,
        "num_pages": paginator.num_pages,
        "start_index": (articles.start_index() - 1) if articles.start_index() else 0,
        "end_index": articles.end_index(),
        "titre_table": "1.1 - Liste des Nouveaux Articles",
        "url_validation": reverse("articles:articles_new_validation"),
        "url_redirect": reverse("articles:new_articles_list"),
    }
    return render(request, "articles/articles_news.html", context=context)


@transaction.atomic
def articles_new_validation(request):
    """Validation des nouveaux articles en masse"""

    # On met à jour les articles sans axes ou en erreur de rubrique presta avant affichage
    with connection.cursor() as cursor:
        cursor.execute(SQL_FLAG_ERROR_SUB_CATEGORY)
        cursor.execute(SQL_FLAG_WITHOUT_AXES)

    articles_object = Article.objects.filter(
        Q(new_article=True)
        | Q(error_sub_category=True)
        | Q(axe_bu__isnull=True)
        | Q(axe_prj__isnull=True)
        | Q(axe_pro__isnull=True)
        | Q(axe_pys__isnull=True)
        | Q(axe_rfa__isnull=True)
        | Q(big_category__isnull=True)
    ).values(
        "pk",
    )

    nb_articles = articles_object.count()

    if request.method == "POST" and nb_articles:
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
        change = ChangesTrace(
            action_datetime=timezone.now(),
            action_type=2,
            function_name=inspect.currentframe(),
            action_by=request.user,
            before={"articles": list(articles.values_list("pk", flat=True))},
            after={"articles": list(articles.values_list("pk", flat=True))},
            difference={"avant": {"new_article": "true"}, "après": {"new_article": "false"}},
            model_name=Article._meta.model_name,
            model=Article._meta.model,
            db_table=Article._meta.db_table,
        )

        nb_updates = articles.update(
            new_article=False, modified_by=request.user, modified_at=timezone.now()
        )
        level = 20

        # On met à jour les articles qui étaient dans edi_ediimport
        with connection.cursor() as cursor:
            cursor.execute(SQL_EDI_IMPORT_ARTICLES)

        # On met à jour les comptes comptable des articles
        set_update_articles_confict_account()

        if nb_articles == nb_updates:
            message = f"Tous les articles ont étés mis à jour ({nb_articles})"
            change.save()
        else:
            level = 50

            if nb_updates:
                change.save()

            message = (
                f"Il reste des articles qui comporte des erreus. "
                f"Articles mis à jour : {nb_updates} / {nb_articles}"
            )

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
        LOGGER_EXPORT_EXCEL.exception("view : articles_news_export_list")

    return redirect(reverse("articles:new_articles_list"))
