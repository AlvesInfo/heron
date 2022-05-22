from django.urls import path

from apps.book.views import (
    SocietiesList,
    SocietyUpdate,
    export_list_societies,
)

app_name = "apps.book"

urlpatterns = [
    path("societies_list/", SocietiesList.as_view(), name="societies_list"),
    path("society_update/<int:pk>/", SocietyUpdate.as_view(), name="society_update"),
    path("excel_outputs/<str:file_name>/", export_list_societies, name="excel_outputs"),
]
