from django.urls import path

from apps.compta.views import (
    # LAUNCH SUBSCRIPTIONS
    royalties_launch,
    meuleuse_launch,
    publicity_launch,
    services_launch,
    # SALES COSIUM
    export_sales_cosium,
)

app_name = "apps.compta"

urlpatterns = (
    # LAUNCH SUBSCRIPTIONS
    [
        path("royalties_launch/", royalties_launch, name="royalties_launch"),
        path("meuleuse_launch/", meuleuse_launch, name="meuleuse_launch"),
        path("publicity_launch/", publicity_launch, name="publicity_launch"),
        path("services_launch/", services_launch, name="services_launch"),
    ]
    # SALES COSIUM
    + [
        path("export_sales_cosium/", export_sales_cosium, name="export_sales_cosium"),
    ]
)
