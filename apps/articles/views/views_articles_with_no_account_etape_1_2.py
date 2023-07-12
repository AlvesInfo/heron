# pylint: disable=E0401,W0702
"""
Views des Articles sans comptes comptables
"""
import pendulum
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect, reverse

from heron.loggers import LOGGER_EXPORT_EXCEL
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.core.functions.functions_http import get_pagination_buttons
from apps.articles.excel_outputs.output_excel_articles_without_account_list import (
    excel_liste_articles_without_account,
)
from apps.articles.parameters.querysets import articles_without_account_queryset
from apps.centers_purchasing.bin.update_account_article import (
    set_update_articles_confict_account,
    update_axes_edi,
)


# ECRANS DES ARTICLES SANS COMPTES COMPTABLES EN ACHATS ET VENTES ==================================
def articles_without_account_list(request):
    """Affichage de tous les articles qui n'ont pas de comptes comptables X3, présents
    dans les imports
    """
    page = request.GET.get("page")

    if page is None:
        # On met à jour les comptes comptable des articles
        set_update_articles_confict_account()

        # Mise à jour des articles de la table edi_ediimport avec les axes de la table articles
        update_axes_edi()

    limit = 100
    # print(str(articles_without_account_queryset.query))
    paginator = Paginator(articles_without_account_queryset, limit)

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
        "titre_table": (
            f'1.2 - Articles sans comptes'
        ),
        # "url_validation": reverse("articles:articles_new_validation"),
        "url_redirect": reverse("articles:articles_without_account_list"),
    }
    return render(request, "articles/articles_without_account.html", context=context)


def articles_without_account_export_list(_):
    """
    Export Excel de la liste des Sociétés
    :param _: Request Django
    :return: response_file
    """
    try:
        today = pendulum.now()
        file_name = (
            f"LISTING_DES_ARTICLES_SANS_COMPTES_{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"
        )

        return response_file(excel_liste_articles_without_account, file_name, CONTENT_TYPE_EXCEL)

    except:
        print('exception("view : articles_without_account_export_list")')
        LOGGER_EXPORT_EXCEL.exception("view : articles_without_account_export_list")

    return redirect(reverse("articles:articles_without_account_list"))
