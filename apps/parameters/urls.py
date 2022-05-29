from django.urls import path

from apps.parameters.views import (
    CategoriesList,
    CategoryCreate,
    CategoryUpdate,
    categories_export_list,
)

app_name = "apps.parameters"

urlpatterns = [
    # Catégories
    path("categories_list/", CategoriesList.as_view(), name="categories_list"),
    path("category_create/", CategoryCreate.as_view(), name="category_create"),
    path("category_update/<int:pk>/", CategoryUpdate.as_view(), name="category_update"),
    path("categories_export_list/", categories_export_list, name="categories_export_list"),
]
