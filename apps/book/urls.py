from django.urls import path

from apps.book.views import (
    SocietiesList,
    society_view,
    export_list_societies,
)

app_name = "apps.book"

urlpatterns = [
    path("societies_list/", SocietiesList.as_view(), name="societies_list"),
    path("society/<str:pk>/", society_view, name="society"),
    path("excel_outputs/<str:file_name>/", export_list_societies, name="excel_outputs"),
]
