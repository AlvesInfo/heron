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
from django.contrib import messages

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
from apps.invoices.models import InvoiceCommonDetails
from apps.invoices.forms import InvoiceSearchForm
from apps.invoices.filters import InvoiceFilter
from apps.invoices.bin.pre_controls import control_insertion


def invoice_search_list(request):
    """Affichage de la page de recherche des Factures pour la réaffectation"""
    limit = 50

    # On contrôle qu'il n'y ait pas des factures non finalisées, mais envoyées par mail
    not_finalize = control_insertion()

    if not_finalize:
        request.session["level"] = 50
        messages.add_message(
            request,
            50,
            (
                "Vous ne pouvez pas ré-affecter des factures, "
                "car la facturation est déjà envoyée par mail, mais non finalisée"
            ),
        )
        context = {
            "margin_table": 50,
            "titre_table": f'Recherche ré-affectation Facture',
            "not_finalize": True,
            "chevron_retour": reverse("home"),
        }
        return render(request, "invoices/invoices_search.html", context=context)

    queryset = (
        InvoiceCommonDetails.objects.values(
            "import_uuid_identification",
            "third_party_num",
            "third_party_num__name",
            "invoice_number",
            "invoice_year",
            "cct",
        )
        .order_by(
            "third_party_num", "invoice_number", "cct",
        )
    )
    invoices_filter = InvoiceFilter(request.GET, queryset=queryset)
    attrs_filter = dict(invoices_filter.data.items())
    paginator = Paginator(invoices_filter.qs, limit)
    page = request.GET.get("page")
    form = InvoiceSearchForm(attrs_filter)

    try:
        invoices = paginator.page(page)
    except PageNotAnInteger:
        invoices = paginator.page(1)
    except EmptyPage:
        invoices = paginator.page(paginator.num_pages)

    count = invoices_filter.qs.count()
    titre_count = ""

    if count == 1:
        titre_count = " (1 Facture trouvé)"

    if count > 1:
        titre_count = f" ({str(count)} Facture trouvés)"

    context = {
        "invoices": paginator.get_page(page),
        "filter": invoices_filter,
        "pagination": get_pagination_buttons(
            invoices.number, paginator.num_pages, nbre_boutons=5, position_color="cadetblue"
        ),
        "num_items": paginator.count,
        "num_pages": paginator.num_pages,
        "start_index": (invoices.start_index() - 1) if invoices.start_index() else 0,
        "end_index": invoices.end_index(),
        "titre_table": f'Recherche réaffectation Facture <span style="font-size: .8em;">{titre_count}</span>',
        "url_redirect": reverse("invoices:invoice_search_list"),
        "attrs_filter": attrs_filter,
        "form": form,
    }
    return render(request, "invoices/invoices_search.html", context=context)
