from django.urls import path

from apps.rfa.views import (
    # Catégories
    SignboardExclusionList,
    SignboardExclusionCreate,
    SignboardExclusionUpdate,
    signboard_exclusion_delete,
    signboard_exclusion_export_list,
    # # MaisonExclusion
    ClientExclusionList,
    ClientExclusionCreate,
    ClientExclusionUpdate,
    client_exclusion_delete,
    client_exclusion_export_list,
    # RateSupplier
    SupplierRateList,
    SupplierRateCreate,
    SupplierRateUpdate,
    supplier_rate_delete,
    supplier_rate_export_list,
    # # SectionRfa
    SectionRfaList,
    SectionRfaCreate,
    SectionRfaUpdate,
    section_rfa_delete,
    section_rfa_export_list,
    # SectionProExclusion
    SectionProExclusionList,
    SectionProExclusionCreate,
    SectionProExclusionUpdate,
    section_pro_exlusion_delete,
    section_pro_exclusions_export_list,
    # RFA GENERATION
    rfa_generation
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
            "signboard_exclusion_delete/",
            signboard_exclusion_delete,
            name="signboard_exclusion_delete",
        ),
        path(
            "signboard_exclusion_export_list/",
            signboard_exclusion_export_list,
            name="signboard_exclusion_export_list",
        ),
    ],
    # MaisonExclusion
    *[
        path(
            "clients_exclusion_list/", ClientExclusionList.as_view(), name="clients_exclusion_list"
        ),
        path(
            "client_exclusion_create/",
            ClientExclusionCreate.as_view(),
            name="client_exclusion_create",
        ),
        path(
            "client_exclusion_update/<int:pk>/",
            ClientExclusionUpdate.as_view(),
            name="client_exclusion_update",
        ),
        path(
            "client_exclusion_delete/",
            client_exclusion_delete,
            name="client_exclusion_delete",
        ),
        path(
            "client_exclusion_export_list/",
            client_exclusion_export_list,
            name="client_exclusion_export_list",
        ),
    ],
    # RateSupplier
    *[
        path(
            "suppliers_rate_list/",
            SupplierRateList.as_view(),
            name="suppliers_rate_list",
        ),
        path(
            "supplier_rate_create/",
            SupplierRateCreate.as_view(),
            name="supplier_rate_create",
        ),
        path(
            "supplier_rate_update/<int:pk>/",
            SupplierRateUpdate.as_view(),
            name="supplier_rate_update",
        ),
        path(
            "supplier_rate_delete/",
            supplier_rate_delete,
            name="supplier_rate_delete",
        ),
        path(
            "suppliers_rate_export_list/",
            supplier_rate_export_list,
            name="suppliers_rate_export_list",
        ),
    ],
    # SectionRfa
    *[
        path(
            "sections_rfa_list/",
            SectionRfaList.as_view(),
            name="sections_rfa_list",
        ),
        path(
            "section_rfa_create/",
            SectionRfaCreate.as_view(),
            name="section_rfa_create",
        ),
        path(
            "section_rfa_update/<int:pk>/",
            SectionRfaUpdate.as_view(),
            name="section_rfa_update",
        ),
        path(
            "section_rfa_delete/",
            section_rfa_delete,
            name="section_rfa_delete",
        ),
        path(
            "section_rfa_export_list/",
            section_rfa_export_list,
            name="section_rfa_export_list",
        ),
    ],
    # SectionProExclusion
    *[
        path(
            "sections_pro_exclusions_list/",
            SectionProExclusionList.as_view(),
            name="sections_pro_exclusions_list",
        ),
        path(
            "section_pro_exclusion_create/",
            SectionProExclusionCreate.as_view(),
            name="section_pro_exclusion_create",
        ),
        path(
            "section_pro_exclusion_update/<int:pk>/",
            SectionProExclusionUpdate.as_view(),
            name="section_pro_exclusion_update",
        ),
        path(
            "section_pro_exlusion_delete/",
            section_pro_exlusion_delete,
            name="section_pro_exlusion_delete",
        ),
        path(
            "section_pro_exclusions_export_list/",
            section_pro_exclusions_export_list,
            name="section_pro_exclusions_export_list",
        ),
    ],
    # RFA GENERATION
    *[
        path(
            "rfa_generation/",
            rfa_generation,
            name="rfa_generation",
        ),
    ],
]
