from django.urls import path

from apps.book.views import (
    SuppliersList,
    export_list_societies,
)

app_name = "apps.book"

urlpatterns = [
    path("supplier_list/", SuppliersList.as_view(), name="supplier_list"),
    path("export_list_societies/", export_list_societies, name="export_list_societies"),
]
