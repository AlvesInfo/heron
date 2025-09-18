from django.urls import path

from apps.book.views import (
    # Tiers
    SocietiesList,
    SocietiesInUseList,
    SocietyUpdate,
    supplier_cct_identifier,
    change_supplier_cct_unit,
    export_list_societies,
    export_list_supplier_cct,
    # Statistiques
    StatistiquesList,
    StatistiqueCreate,
    StatistiqueUpdate,
    statistiques_export_list,
    # Familles/Axes
    FamillyAxeCreate,
    FamillyAxeUpdate,
    delete_familly_axes,
)

app_name = "apps.book"

urlpatterns = [
    # Tiers
    *[
        path("societies_list/", SocietiesList.as_view(), name="societies_list"),
        path("societies_list_in_use/", SocietiesInUseList.as_view(), name="societies_list_in_use"),
        path(
            "society_update/<int:pk>/<str:in_use>/", SocietyUpdate.as_view(), name="society_update"
        ),
        path(
            "update_supplier_cct_identifier/<str:third_party_num>/<str:url_retour_supplier_cct>/",
            supplier_cct_identifier,
            name="supplier_cct_identifier",
        ),
        path(
            "change_supplier_cct_unit/", change_supplier_cct_unit, name="change_supplier_cct_unit"
        ),
        path("excel_outputs/<str:file_name>/", export_list_societies, name="excel_outputs"),
        path(
            "export_list_supplier_cct/<str:third_party_num>/",
            export_list_supplier_cct,
            name="export_list_supplier_cct",
        ),
    ],
    # Statistiques
    *[
        path("statistiques_list/", StatistiquesList.as_view(), name="statistiques_list"),
        path("statistique_create/", StatistiqueCreate.as_view(), name="statistique_create"),
        path(
            "statistique_update/<slug:name>/",
            StatistiqueUpdate.as_view(),
            name="statistique_update",
        ),
        path(
            "statistiques_export_list/", statistiques_export_list, name="statistiques_export_list"
        ),
    ],
    # Familles/Axes
    *[
        path(
            "familly_axes_create/<int:statistique_pk>/",
            FamillyAxeCreate.as_view(),
            name="familly_axes_create",
        ),
        path(
            "familly_axes_update/<int:statistique_pk>/<int:pk>/",
            FamillyAxeUpdate.as_view(),
            name="familly_axes_update",
        ),
        path(
            "delete_familly_axes/",
            delete_familly_axes,
            name="delete_familly_axes",
        ),
    ],
]
