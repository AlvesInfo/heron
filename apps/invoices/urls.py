"""Routes URL de l'application invoices."""

from django.urls import path

from apps.invoices.views import (
    AxesDetailsCreate,
    # Axe Pro / Entête détails facturation
    AxesDetailsList,
    AxesDetailsUpdate,
    EntetesDetailsCreate,
    # Entête détails facturation
    EntetesDetailsList,
    EntetesDetailsUpdate,
    ExportX3Files,
    axes_details_delete,
    axes_details_export_list,
    entetes_details_delete,
    entetes_details_export_list,
    export_achats,
    finalize_period,
    generate_exports_x3,
    generate_facturx_invoice,
    # Insertion et Génération des factures en PDF
    generate_invoices_insertions,
    generate_pdf_invoice,
    get_export_x3_file,
    get_pdf_file,
    # Réaffectations de factures
    invoice_search_list,
    invoices_pdf_files,
    send_email_pdf_invoice,
    valid_export_achats,
)

# Les vues SSE d'envoi d'emails (api_gmail.views_sse) seront routées après la configuration Gmail

app_name = "apps.invoices"

urlpatterns = [
    # Axe Pro / Entête détails facturation
    *[
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
    ],
    # Axe Pro / Entête détails facturation
    *[
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
    ],
    # Insertion et Génération des factures en PDF
    *[
        path(
            "generate_invoices_insertions/",
            generate_invoices_insertions,
            name="generate_invoices_insertions",
        ),
        path("generate_pdf_invoice/", generate_pdf_invoice, name="generate_pdf_invoice"),
        path(
            "generate_facturx_invoice/",
            generate_facturx_invoice,
            name="generate_facturx_invoice",
        ),
        path("invoices_pdf_files/", invoices_pdf_files, name="invoices_pdf_files"),
        path("get_pdf_file/<str:file_name>", get_pdf_file, name="get_pdf_file"),
        path("send_email_pdf_invoice/", send_email_pdf_invoice, name="send_email_pdf_invoice"),
        path("generate_exports_X3/", generate_exports_x3, name="generate_exports_X3"),
        path("export_x3_files/", ExportX3Files.as_view(), name="export_x3_files"),
        path("get_export_x3_file/<str:file_name>", get_export_x3_file, name="get_export_x3_file"),
        path("finalize_period/", finalize_period, name="finalize_period"),
        path("valid_export_achats/", valid_export_achats, name="valid_export_achats"),
        path("export_achats/", export_achats, name="export_achats"),
    ],
    # Réaffectations de factures
    *[
        path(
            "invoice_search_list/",
            invoice_search_list,
            name="invoice_search_list",
        ),
    ],
]
