from django.urls import path

from apps.centers_clients.views import (
    MaisonsList,
    import_bi,
    filter_list_maisons_api,
    MaisonCreate,
    MaisonUpdate,
    maisons_export_list,
    MaisonSupllierExclusionList,
    MaisonSupllierExclusionCreate,
    MaisonSupllierExclusionUpdate,
    exclusion_delete,
    exclusion_export_list,
)

app_name = "apps.centers_clients"

urlpatterns = [
    *[
        # MAISONS
        path("maisons_list/", MaisonsList.as_view(), name="maisons_list"),
        path("import_bi/", import_bi, name="import_bi"),
        path("filter_list_maisons_api/", filter_list_maisons_api, name="filter_list_maisons_api"),
        path("maisons_create/<str:initials>/", MaisonCreate.as_view(), name="maisons_create"),
        path("maisons_update/<int:pk>/", MaisonUpdate.as_view(), name="maisons_update"),
        path("maisons_export_list/", maisons_export_list, name="maisons_export_list"),
    ],
    *[
        # EXCLUSIONS TIERS X3 / MAISONS
        path("exclusions_list/", MaisonSupllierExclusionList.as_view(), name="exclusions_list"),
        path("exclusion_create/", MaisonSupllierExclusionCreate.as_view(), name="exclusion_create"),
        path(
            "exclusion_update/<int:pk>/",
            MaisonSupllierExclusionUpdate.as_view(),
            name="exclusion_update",
        ),
        path("exclusion_delete/<int:pk>/", exclusion_delete, name="exclusion_update"),
        path("exclusion_export_list/", exclusion_export_list, name="exclusion_export_list"),
    ],
    *[
        # EXCLUSIONS MAISONS / PAYS
        path(
            "exclusions_country_list/",
            MaisonSupllierExclusionList.as_view(),
            name="exclusions_country_list",
        ),
        path(
            "exclusion_country_create/",
            MaisonSupllierExclusionCreate.as_view(),
            name="exclusion_country_create",
        ),
        path(
            "exclusion_country_update/<int:pk>/",
            MaisonSupllierExclusionUpdate.as_view(),
            name="exclusion_country_update",
        ),
        path(
            "exclusion_country_delete/<int:pk>/", exclusion_delete, name="exclusion_country_update"
        ),
        path(
            "exclusion_country_export_list/",
            exclusion_export_list,
            name="exclusion_country_export_list",
        ),
    ],
]
