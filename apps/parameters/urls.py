from django.urls import path

from apps.parameters.views import (
    CategoriesList,
    CategoryCreate,
    CategoryUpdate,
    categories_export_list,
    SubCategoryCreate,
    SubCategoryUpdate,
    DefaultAxeAricleUpdate,
    axe_articles_defaut_export_list,
)

app_name = "apps.parameters"

urlpatterns = [
    # Catégories
    path("categories_list/", CategoriesList.as_view(), name="categories_list"),
    path("category_create/", CategoryCreate.as_view(), name="category_create"),
    path("category_update/<int:pk>/", CategoryUpdate.as_view(), name="category_update"),
    path("categories_export_list/", categories_export_list, name="categories_export_list"),
    # Rubriques Presta
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
    # Catégories et Axes par défaut pourl es articles
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
]
