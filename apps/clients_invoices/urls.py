from django.urls import path

from apps.clients_invoices.views import pdf_view

urlpatterns = [
    *[
        # TEST DES FACTURES EN PDF
        path("pdf_test/", pdf_view, name="pdf_test"),
    ],
    *[],
]
