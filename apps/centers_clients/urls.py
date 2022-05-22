from django.urls import path

from apps.centers_clients.views import (
    clients,
    MaisonsList,
    import_bi,
    filter_list_maisons_api,
    MaisonCreate,
    MaisonUpdate,
    maisons_export_list,
)

app_name = "apps.centers_clients"

urlpatterns = [
    path("clients_home/", clients, name="clients_home"),
    path("maisons_list/", MaisonsList.as_view(), name="maisons_list"),
    path("import_bi/", import_bi, name="import_bi"),
    path("filter_list_maisons_api/", filter_list_maisons_api, name="filter_list_maisons_api"),
    path("maisons_create/<str:initials>/", MaisonCreate.as_view(), name="maisons_create"),
    path("maisons_update/<int:pk>/", MaisonUpdate.as_view(), name="maisons_update"),
    path("maisons_export_list/", maisons_export_list, name="maisons_export_list"),
]
