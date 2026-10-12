"""Views pour réafecter sur une facture, précédente, soit un mauvais code de la part du fournisseur,.

ou une mauvaise affectation de l'opérateur qui a effectué la facturationion précédente.

Commentaire:

created at: 2023-07-07
created by: Paulo ALVES

modified at: 2023-07-07
modified by: Paulo ALVES
"""

from django.contrib import messages
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import render
from django.urls import reverse
from django.utils.html import format_html

from apps.core.functions.functions_http import get_pagination_buttons
from apps.invoices.bin.pre_controls import control_insertion
from apps.invoices.filters import InvoiceFilter
from apps.invoices.forms import InvoiceSearchForm
from apps.invoices.models import InvoiceCommonDetails


def invoice_search_list(request):
    """Affichage de la page de recherche des Factures pour la réaffectation."""
    limit = 50

    # On contrôle qu'il n'y ai pas des factures non finalisées, mais envoyées par mail
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
            "titre_table": "Recherche ré-affectation Facture",
            "not_finalize": True,
            "chevron_retour": reverse("home"),
        }
        return render(request, "invoices/invoices_search.html", context=context)

    queryset = InvoiceCommonDetails.objects.values(
        "import_uuid_identification",
        "third_party_num",
        "third_party_num__name",
        "invoice_number",
        "invoice_year",
        "cct",
    ).order_by(
        "third_party_num",
        "invoice_number",
        "cct",
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
        titre_count = f" ({count!s} Facture trouvés)"

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
        "titre_table": format_html(
            'Recherche réaffectation Facture <span style="font-size: .8em;">{}</span>', titre_count
        ),
        "url_redirect": reverse("invoices:invoice_search_list"),
        "attrs_filter": attrs_filter,
        "form": form,
    }
    return render(request, "invoices/invoices_search.html", context=context)
