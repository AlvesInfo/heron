from django.urls import path

from apps.data_flux.views import (
    # Import de fichiers
    processing_files
)

app_name = "apps.data_flux"

urlpatterns = [
    # Import de fichiers
    *[
        path("processing_files/<str:function_name>/", processing_files, name="processing_files"),
    ],
]
