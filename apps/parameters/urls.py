from django.urls import path

from apps.parameters.views import (
    # Catégories
    CategoriesList,
    CategoryCreate,
    CategoryUpdate,
    categories_export_list,
    # Rubriques Presta
    SubCategoryCreate,
    SubCategoryUpdate,
    delete_sub_category,
    # Catégories et Axes par défaut pour les articles
    DefaultAxeAricleUpdate,
    axe_articles_defaut_export_list,
    # Function pour la génération des factures
    FunctionsList,
    FunctionCreate,
    FunctionUpdate,
    functions_export_list,
    function_delete,
    # Numérotation
    NumberingsList,
    NumberingCreate,
    NumberingUpdate,
    numberings_export_list,
    numbering_delete,
    # NATURE/GENRE
    NaturesList,
    NatureCreate,
    NatureUpdate,
    natures_export_list,
    nature_delete,
)

app_name = "apps.parameters"

urlpatterns = [
    # Catégories
    *[
        path("categories_list/", CategoriesList.as_view(), name="categories_list"),
        path("category_create/", CategoryCreate.as_view(), name="category_create"),
        path("category_update/<int:pk>/", CategoryUpdate.as_view(), name="category_update"),
        path("categories_export_list/", categories_export_list, name="categories_export_list"),
    ],
    # Rubriques Presta
    *[
        path(
            "sub_category_create/<int:category_pk>/",
            SubCategoryCreate.as_view(),
            name="sub_category_create",
        ),
        path(
            "sub_category_update/<int:category_pk>/<int:pk>/",
            SubCategoryUpdate.as_view(),
            name="sub_category_update",
        ),
        path(
            "delete_sub_category/",
            delete_sub_category,
            name="delete_sub_category",
        ),
    ],
    # Catégories et Axes par défaut pour les articles
    *[
        path(
            "axes_articles_defaut/<str:slug_name>/",
            DefaultAxeAricleUpdate.as_view(),
            name="axes_articles_defaut",
        ),
        path(
            "axe_articles_defaut_export_list/",
            axe_articles_defaut_export_list,
            name="axe_articles_defaut_export_list",
        ),
    ],
    # Function pour la génération des factures
    *[
        path("functions_list/", FunctionsList.as_view(), name="functions_list"),
        path(
            "function_create/",
            FunctionCreate.as_view(),
            name="function_create",
        ),
        path(
            "function_update/<int:pk>/",
            FunctionUpdate.as_view(),
            name="function_update",
        ),
        path("functions_export_list/", functions_export_list, name="functions_export_list"),
        path("function_delete/", function_delete, name="function_delete"),
    ],
    # Numérotation
    *[
        path("numberings_list/", NumberingsList.as_view(), name="numberings_list"),
        path("numbering_create/", NumberingCreate.as_view(), name="numbering_create"),
        path("numbering_update/<int:pk>/", NumberingUpdate.as_view(), name="numbering_update"),
        path("numberings_export_list/", numberings_export_list, name="numberings_export_list"),
        path("numbering_delete/", numbering_delete, name="numbering_delete"),
    ],
    # NATURE/GENRE
    *[
        path("natures_list/", NaturesList.as_view(), name="natures_list"),
        path("nature_create/", NatureCreate.as_view(), name="nature_create"),
        path("nature_update/<int:pk>/", NatureUpdate.as_view(), name="nature_update"),
        path("natures_export_list/", natures_export_list, name="natures_export_list"),
        path("nature_delete/", nature_delete, name="nature_delete"),
    ],
]
