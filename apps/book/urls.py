from django.urls import path

from apps.book.views import (
    SocietiesList,
    UpdateSupplier,
    export_list_societies,
)

app_name = "apps.book"

urlpatterns = [
    path("societies_list/", SocietiesList.as_view(), name="societies_list"),
    path("update_supplier/<int:pk>/", UpdateSupplier.as_view(), name="update_supplier"),
    path("export_list_societies/", export_list_societies, name="export_list_societies"),
]
