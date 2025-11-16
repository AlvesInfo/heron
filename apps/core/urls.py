from django.urls import path


from apps.core.views import (
    # TEST DES FACTURES EN PDF
    pdf_view,
    # API POUR LES DROPDOWN SEMANTIC
    api_models_query,
    # API POUR LES DROPDOWN SEMANTIC
    api_models_query_third_party_num,
    # API POUR LES JAUGES AJAX POLLING
    get_user_jobs,
    get_active_jobs,
    get_job_progress,
    delete_job,
)

urlpatterns = [
    # TEST DES FACTURES EN PDF
    *[
        path("pdf_test/", pdf_view, name="pdf_test"),
    ],
    # API POUR LES DROPDOWN SEMANTIC
    *[
        path(
            "api_models_query/<str:models>/<str:query>/",
            api_models_query,
            name="api_models_query",
        ),
    ],
    # API POUR LES DROPDOWN SEMANTIC
    *[
        path(
            "api_models_query/<str:models>/<str:third_party_num>/<str:query>/",
            api_models_query_third_party_num,
            name="api_models_query_third_party_num",
        ),
    ],
    # API POUR LES JAUGES AJAX POLLING
    path("sse-progress/", get_user_jobs, name="list_jobs"),
    path("sse-progress/active/", get_active_jobs, name="active_jobs"),
    path("sse-progress/<str:job_id>/", get_job_progress, name="job_detail"),
    path("sse-progress/<str:job_id>/delete/", delete_job, name="delete_job"),
]
