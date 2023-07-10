from django.urls import path

from apps.invoices.views import (
    # Entête détails facturation
    EntetesDetailsList,
    EntetesDetailsCreate,
    EntetesDetailsUpdate,
    entetes_details_delete,
    entetes_details_export_list,
    # Axe Pro / Entête détails facturation
    AxesDetailsList,
    AxesDetailsCreate,
    AxesDetailsUpdate,
    axes_details_delete,
    axes_details_export_list,
    # Insertion et Génération des factures en PDF
    generate_invoices_insertions,
    generate_pdf_invoice,
    send_email_pdf_invoice,
    # Réaffectations de factures
    invoice_search_list,
)

app_name = "apps.invoices"

urlpatterns = (
    # Axe Pro / Entête détails facturation
    [
        path("entete_details_list/", EntetesDetailsList.as_view(), name="entete_details_list"),
        path(
            "entete_details_create/", EntetesDetailsCreate.as_view(), name="entete_details_create"
        ),
        path(
            "entete_details_update/<int:pk>/",
            EntetesDetailsUpdate.as_view(),
            name="entete_details_update",
        ),
        path("entete_details_delete/", entetes_details_delete, name="entete_details_delete"),
        path(
            "entete_details_export_list/",
            entetes_details_export_list,
            name="entete_details_export_list",
        ),
    ]
    # Axe Pro / Entête détails facturation
    + [
        path("axes_details_list/", AxesDetailsList.as_view(), name="axes_details_list"),
        path("axes_details_create/", AxesDetailsCreate.as_view(), name="axes_details_create"),
        path(
            "axes_details_update/<int:pk>/",
            AxesDetailsUpdate.as_view(),
            name="axes_details_update",
        ),
        path("axes_details_delete/", axes_details_delete, name="axes_details_delete"),
        path(
            "axes_details_export_list/",
            axes_details_export_list,
            name="axes_details_export_list",
        ),
    ]
    # Insertion et Génération des factures en PDF
    + [
        path(
            "generate_invoices_insertions/",
            generate_invoices_insertions,
            name="generate_invoices_insertions",
        ),
        path("generate_pdf_invoice/", generate_pdf_invoice, name="generate_pdf_invoice"),
        path("send_email_pdf_invoice/", send_email_pdf_invoice, name="send_email_pdf_invoice"),
    ]
    # Réaffectations de factures
    + [
        path(
            "invoice_search_list/",
            invoice_search_list,
            name="invoice_search_list",
        ),
    ]
)
