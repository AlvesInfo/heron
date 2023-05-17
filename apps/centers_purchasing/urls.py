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
    # Type de Facture par centrale fille
    TypeFactureList,
    TypeFactureCreate,
    TypeFactureUpdate,
    type_facture_delete,
    # Regroupement factures
    GroupingGoodsList,
    GroupingGoodsCreate,
    GroupingGoodsUpdate,
    grouping_goods_delete,
    grouping_goods_export_list,
    # Axe Pro / regroupement facturation
    AxeGroupingList,
    AxeGroupingCreate,
    AxeGroupingUpdate,
    axe_grouping_delete,
    axe_grouping_export_list,
    # Comptes par Centrale fille, Catégorie, Axe Pro, et TVA
    account_axe_list,
    AccountAxeCreate,
    AccountAxeUpdate,
    account_axe_delete,
    account_axe_import_file,
    account_axe_export_list,
    # Dictionnaire Centrale Filles/Axe Pro/TVA
    AxeProVatList,
    AxeProVatCreate,
    AxeProVatUpdate,
    axe_pro_vat_delete,
    axe_pro_vat_export_list,
)

app_name = "apps.centers_purchasing"

urlpatterns = (
    # Centrales Mères
    [
        path("meres_list/", MeresList.as_view(), name="meres_list"),
        path("mere_create/", MereCreate.as_view(), name="mere_create"),
        path("mere_update/<int:pk>/", MereUpdate.as_view(), name="mere_update"),
        path("meres_export_list/", meres_export_list, name="meres_export_list"),
    ]
    # Centrales Filles
    + [
        path("filles_list/", FillesList.as_view(), name="filles_list"),
        path("fille_create/", FilleCreate.as_view(), name="fille_create"),
        path("fille_update/<int:pk>/", FilleUpdate.as_view(), name="fille_update"),
        path("filles_export_list/", filles_export_list, name="filles_export_list"),
    ]
    # Type de Facture par centrale fille
    + [
        path("type_facture_list/", TypeFactureList.as_view(), name="type_facture_list"),
        path("type_facture_create/", TypeFactureCreate.as_view(), name="type_facture_create"),
        path(
            "type_facture_update/<int:pk>/", TypeFactureUpdate.as_view(), name="type_facture_update"
        ),
        path("type_facture_delete/", type_facture_delete, name="type_facture_delete"),
    ]
    # Enseignes
    + [
        path("enseignes_list/", EnseignesList.as_view(), name="enseignes_list"),
        path("enseigne_create/", EnseigneCreate.as_view(), name="enseigne_create"),
        path("enseigne_update/<int:pk>/", EnseigneUpdate.as_view(), name="enseigne_update"),
        path("enseignes_export_list/", enseignes_export_list, name="enseignes_export_list"),
    ]
    # Regroupement factures
    + [
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
    # Axe Pro / regroupement facturation
    + [
        path("axe_grouping_list/", AxeGroupingList.as_view(), name="axe_grouping_list"),
        path("axe_grouping_create/", AxeGroupingCreate.as_view(), name="axe_grouping_create"),
        path(
            "axe_grouping_update/<int:pk>/",
            AxeGroupingUpdate.as_view(),
            name="axe_grouping_update",
        ),
        path("axe_grouping_delete/", axe_grouping_delete, name="axe_grouping_delete"),
        path(
            "axe_grouping_export_list/",
            axe_grouping_export_list,
            name="axe_grouping_export_list",
        ),
    ]
    # Comptes par Centrale fille, Catégorie, Axe Pro, et TVA
    + [
        path("account_axe_list/", account_axe_list, name="account_axe_list"),
        path("account_axe_create/", AccountAxeCreate.as_view(), name="account_axe_create"),
        path(
            "account_axe_update/<int:pk>/",
            AccountAxeUpdate.as_view(),
            name="account_axe_update",
        ),
        path("account_axe_delete/", account_axe_delete, name="account_axe_delete"),
        path(
            "account_axe_import_file/",
            account_axe_import_file,
            name="account_axe_import_file",
        ),
        path(
            "account_axe_export_list/",
            account_axe_export_list,
            name="account_axe_export_list",
        ),
    ]
    # Dictionnaire Centrale Filles/Axe Pro/TVA
    + [
        path("axe_pro_vat_list/", AxeProVatList.as_view(), name="axe_pro_vat_list"),
        path("axe_pro_vat_create/", AxeProVatCreate.as_view(), name="axe_pro_vat_create"),
        path(
            "axe_pro_vat_update/<int:pk>/",
            AxeProVatUpdate.as_view(),
            name="axe_pro_vat_update",
        ),
        path("axe_pro_vat_delete/", axe_pro_vat_delete, name="axe_pro_vat_delete"),
        path(
            "axe_pro_vat_export_list/",
            axe_pro_vat_export_list,
            name="axe_pro_vat_export_list",
        ),
    ]
)
