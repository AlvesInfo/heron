from django.urls import path

from apps.rfa.views import (
    # Catégories
    SignboardExclusionList,
    SignboardExclusionCreate,
    SignboardExclusionUpdate,
    signboard_exclusion_delete,
    signboard_exclusion_export_list,
    # # MaisonExclusion
    # ClientExclusionList,
    # ClientExclusionCreate,
    # ClientExclusionUpdate,
    # client_exclusion_export_list,
    # # RateSupplier
    # RateSupplierList,
    # RateSupplierCreate,
    # RateSupplierUpdate,
    # rate_supplier_exclusion_export_list,
    # # SectionRfa
    # SectionRfaList,
    # SectionRfaCreate,
    # SectionRfaUpdate,
    # section_rfa_exclusion_export_list,
    # # SectionProExclusion
    # SectionProExclusionList,
    # SectionProExclusionCreate,
    # SectionProExclusionUpdate,
    # section_pro_exclusion_export_list,
)

app_name = "apps.rfa"

urlpatterns = [
    # SignboardExclusion
    *[
        path(
            "signboards_exclusion_list/",
            SignboardExclusionList.as_view(),
            name="signboards_exclusion_list",
        ),
        path(
            "signboard_exclusion_create/",
            SignboardExclusionCreate.as_view(),
            name="signboard_exclusion_create",
        ),
        path(
            "signboard_exclusion_update/<int:pk>/",
            SignboardExclusionUpdate.as_view(),
            name="signboard_exclusion_update",
        ),
        path(
            "signboard_exclusion_export_list/",
            signboard_exclusion_export_list,
            name="signboard_exclusion_export_list",
        ),
        path(
            "signboard_exclusion_delete/",
            signboard_exclusion_delete,
            name="signboard_exclusion_delete",
        ),
    ],
    # # MaisonExclusion
    # *[
    #     path(
    #         "clients_exclusion_list/", ClientExclusionList.as_view(), name="clients_exclusion_list"
    #     ),
    #     path(
    #         "client_exclusion_create/",
    #         ClientExclusionCreate.as_view(),
    #         name="client_exclusion_create",
    #     ),
    #     path(
    #         "client_exclusion_update/<int:pk>/",
    #         ClientExclusionUpdate.as_view(),
    #         name="client_exclusion_update",
    #     ),
    #     path(
    #         "client_exclusion_export_list/",
    #         client_exclusion_export_list,
    #         name="client_exclusion_export_list",
    #     ),
    # ],
    # # RateSupplier
    # *[
    #     path(
    #         "rates_supplier_exclusion_list/",
    #         RateSupplierList.as_view(),
    #         name="rates_supplier_exclusion_list",
    #     ),
    #     path(
    #         "rate_supplier_exclusion_create/",
    #         RateSupplierCreate.as_view(),
    #         name="rate_supplier_exclusion_create",
    #     ),
    #     path(
    #         "rate_supplier_exclusion_update/<int:pk>/",
    #         RateSupplierUpdate.as_view(),
    #         name="rate_supplier_exclusion_update",
    #     ),
    #     path(
    #         "rate_supplier_exclusion_export_list/",
    #         rate_supplier_exclusion_export_list,
    #         name="rate_supplier_exclusion_export_list",
    #     ),
    # ],
    # # SectionRfa
    # *[
    #     path(
    #         "sections_rfa_exclusion_list/",
    #         SectionRfaList.as_view(),
    #         name="sections_rfa_exclusion_list",
    #     ),
    #     path(
    #         "section_rfa_exclusion_create/",
    #         SectionRfaCreate.as_view(),
    #         name="section_rfa_exclusion_create",
    #     ),
    #     path(
    #         "section_rfa_exclusion_update/<int:pk>/",
    #         SectionRfaUpdate.as_view(),
    #         name="section_rfa_exclusion_update",
    #     ),
    #     path(
    #         "section_rfa_exclusion_export_list/",
    #         section_rfa_exclusion_export_list,
    #         name="section_rfa_exclusion_export_list",
    #     ),
    # ],
    # # SectionProExclusion
    # *[
    #     path(
    #         "sections_pro_exclusion_list/",
    #         SectionProExclusionList.as_view(),
    #         name="sections_pro_exclusion_list",
    #     ),
    #     path(
    #         "section_pro_exclusion_create/",
    #         SectionProExclusionCreate.as_view(),
    #         name="section_pro_exclusion_create",
    #     ),
    #     path(
    #         "section_pro_exclusion_update/<int:pk>/",
    #         SectionProExclusionUpdate.as_view(),
    #         name="section_pro_exclusion_update",
    #     ),
    #     path(
    #         "section_pro_exclusion_export_list/",
    #         section_pro_exclusion_export_list,
    #         name="section_pro_exclusion_export_list",
    #     ),
    # ],
]
