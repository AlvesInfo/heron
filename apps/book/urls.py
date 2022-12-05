from django.urls import path

from apps.book.views import (
    SocietiesList,
    SocietyUpdate,
supplier_cct_identifier,
    # SupplierCctIdentifier,
    export_list_societies,
)

app_name = "apps.book"

urlpatterns = [
    path("societies_list/", SocietiesList.as_view(), name="societies_list"),
    path(
        "society_update/<int:pk>/", SocietyUpdate.as_view(), name="society_update"
    ),
    path(
        "supplier_cct_identifier/<str:third_party_num>/",
        supplier_cct_identifier,
        name="supplier_cct_identifier",
    ),
    path("excel_outputs/<str:file_name>/", export_list_societies, name="excel_outputs"),
]
