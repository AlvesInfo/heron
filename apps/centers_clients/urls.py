from django.urls import path

from apps.centers_clients.views import (
    clients,
    MaisonsList,
    filter_list_maisons_api,
    CreateMaison,
    UpdateMaison,
    export_list_maisons,
)

app_name = "apps.centers_clients"

urlpatterns = [
    path("clients_home/", clients, name="clients_home"),
    path("maisons_list/", MaisonsList.as_view(), name="maisons_list"),
    path("filter_list_maisons_api/", filter_list_maisons_api, name="filter_list_maisons_api"),
    path("maisons_create/", CreateMaison.as_view(), name="maisons_create"),
    path("update_maison/<int:pk>/", UpdateMaison.as_view(), name="update_maison"),
    path("export_list_maisons/", export_list_maisons, name="export_list_maisons"),
]
