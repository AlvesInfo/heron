from django.urls import path

from apps.centers_purchasing.views import (
    # Centrales Mères
    MeresList,
    MereCreate,
    MereUpdate,
    meres_export_list,
    # Centrales Filles
    FillesList,
    FilleCreate,
    FilleUpdate,
    filles_export_list,
    # Enseignes
    EnseignesList,
    EnseigneCreate,
    EnseigneUpdate,
    enseignes_export_list,
)

app_name = "apps.centers_purchasing"

urlpatterns = [
    # Centrales Mères
    path("meres_list/", MeresList.as_view(), name="meres_list"),
    path("mere_create/", MereCreate.as_view(), name="mere_create"),
    path("mere_update/<int:pk>/", MereUpdate.as_view(), name="mere_update"),
    path("meres_export_list/", meres_export_list, name="meres_export_list"),
] + [
    # Centrales Filles
    path("filles_list/", FillesList.as_view(), name="filles_list"),
    path("fille_create/", FilleCreate.as_view(), name="fille_create"),
    path("fille_update/<int:pk>/", FilleUpdate.as_view(), name="fille_update"),
    path("filles_export_list/", filles_export_list, name="filles_export_list"),
] + [
    # Enseignes
    path("enseignes_list/", EnseignesList.as_view(), name="enseignes_list"),
    path("enseigne_create/", EnseigneCreate.as_view(), name="enseigne_create"),
    path("enseigne_update/<int:pk>/", EnseigneUpdate.as_view(), name="enseigne_update"),
    path("enseignes_export_list/", enseignes_export_list, name="enseignes_export_list"),
]
