from django.urls import path

from apps.core.views import pdf_view, api_models_query

urlpatterns = [
    # TEST DES FACTURES EN PDF
    *[
        path("pdf_test/", pdf_view, name="pdf_test"),
    ],
    # API POUR LES DROPDOWN SEMANTIC
    *[
        path(
            "api_models_query/<str:models>/<str:query>/", api_models_query, name="api_models_query"
        ),
    ],
]
