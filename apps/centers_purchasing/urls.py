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
    # Regroupement factures
    GroupingGoodsList,
    GroupingGoodsCreate,
    GroupingGoodsUpdate,
    grouping_goods_delete,
    grouping_goods_export_list,
    # Regroupement axe pro familles Acuitis
    AcuitisAxeList,
    AcuitisAxeCreate,
    AcuitisAxeUpdate,
    acuitis_axe_delete,
    acuitis_axe_export_list,
    # Regroupement axe pro familles Cosium
    CosiumAxeList,
    CosiumAxeCreate,
    CosiumAxeUpdate,
    cosium_axe_delete,
    cosium_axe_export_list,
    # Axe Pro / regroupement facturation
    # Comptes par Centrale fille, Catégorie, Axe Pro, et TVA
)

app_name = "apps.centers_purchasing"

urlpatterns = (
    [
        # Centrales Mères
        path("meres_list/", MeresList.as_view(), name="meres_list"),
        path("mere_create/", MereCreate.as_view(), name="mere_create"),
        path("mere_update/<int:pk>/", MereUpdate.as_view(), name="mere_update"),
        path("meres_export_list/", meres_export_list, name="meres_export_list"),
    ]
    + [
        # Centrales Filles
        path("filles_list/", FillesList.as_view(), name="filles_list"),
        path("fille_create/", FilleCreate.as_view(), name="fille_create"),
        path("fille_update/<int:pk>/", FilleUpdate.as_view(), name="fille_update"),
        path("filles_export_list/", filles_export_list, name="filles_export_list"),
    ]
    + [
        # Enseignes
        path("enseignes_list/", EnseignesList.as_view(), name="enseignes_list"),
        path("enseigne_create/", EnseigneCreate.as_view(), name="enseigne_create"),
        path("enseigne_update/<int:pk>/", EnseigneUpdate.as_view(), name="enseigne_update"),
        path("enseignes_export_list/", enseignes_export_list, name="enseignes_export_list"),
    ]
    + [
        # Regroupement factures
        path("grouping_goods_list/", GroupingGoodsList.as_view(), name="grouping_goods_list"),
        path("grouping_goods_create/", GroupingGoodsCreate.as_view(), name="grouping_goods_create"),
        path(
            "grouping_goods_update/<int:pk>/",
            GroupingGoodsUpdate.as_view(),
            name="grouping_goods_update",
        ),
        path("grouping_goods_delete/", grouping_goods_delete, name="grouping_goods_delete"),
        path(
            "grouping_goods_export_list/",
            grouping_goods_export_list,
            name="grouping_goods_export_list",
        ),
    ]
    + [
        # Regroupement axe pro familles Acuitis
        path("acuitis_axe_list/", AcuitisAxeList.as_view(), name="acuitis_axe_list"),
        path("acuitis_axe_create/", AcuitisAxeCreate.as_view(), name="acuitis_axe_create"),
        path(
            "acuitis_axe_update/<int:pk>/",
            AcuitisAxeUpdate.as_view(),
            name="acuitis_axe_update",
        ),
        path("acuitis_axe_delete/", acuitis_axe_delete, name="acuitis_axe_delete"),
        path(
            "acuitis_axe_export_list/",
            acuitis_axe_export_list,
            name="acuitis_axe_export_list",
        ),
    ]
    + [
        # Regroupement axe pro familles Cosium
        path("cosium_axe_list/", CosiumAxeList.as_view(), name="cosium_axe_list"),
        path("cosium_axe_create/", CosiumAxeCreate.as_view(), name="cosium_axe_create"),
        path(
            "cosium_axe_update/<int:pk>/",
            CosiumAxeUpdate.as_view(),
            name="cosium_axe_update",
        ),
        path("cosium_axe_delete/", cosium_axe_delete, name="cosium_axe_delete"),
        path(
            "cosium_axe_export_list/",
            cosium_axe_export_list,
            name="cosium_axe_export_list",
        ),
    ]
    + [
        # Axe Pro / regroupement facturation
    ]
    + [
        # Comptes par Centrale fille, Catégorie, Axe Pro, et TVA
    ]
)
