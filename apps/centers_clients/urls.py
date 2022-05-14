from django.urls import path

from apps.centers_clients.views import (
    MaisonsList,
    CreateMaison,
    UpdateMaison,
    export_list_maisons,
)

app_name = "apps.centers_clients"

urlpatterns = [
    path("maisons_list/", MaisonsList.as_view(), name="maisons_list"),
    path("maisons_create/", CreateMaison.as_view(), name="maisons_create"),
    path("update_maison/<int:pk>/", UpdateMaison.as_view(), name="update_maison"),
    path("export_list_maisons/", export_list_maisons, name="export_list_maisons"),
]
