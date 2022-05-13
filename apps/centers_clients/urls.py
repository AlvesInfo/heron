from django.urls import path

from apps.centers_clients.views import (
    MaisonsList,
    export_list_maisons,
)

app_name = "apps.book"

urlpatterns = [
    path("maisons_list/", MaisonsList.as_view(), name="maisons_list"),
    path("export_list_maisons/", export_list_maisons, name="export_list_maisons"),
]
