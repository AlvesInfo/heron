from django.urls import path

from apps.validation_sales.views import (
    sage_controls_sales,
)

app_name = "apps.validation_sales"

urlpatterns = [
    path("sage_controls_sales/", sage_controls_sales, name="sage_controls_sales"),
]
