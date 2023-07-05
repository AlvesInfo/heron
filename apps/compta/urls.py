from django.urls import path

from apps.compta.views import (
    # LAUNCH SUBSCRIPTIONS
    royalties_launch,
    meuleuse_launch,
    publicity_launch,
    services_launch,
    # SALES COSIUM
    export_sales_cosium,
    export_ca_cosium,
    reset_clients_in_sales,
    reset_exhange_rates_in_sales,
    reset_sales,
    reset_ca,
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
        path("export_ca_cosium/", export_ca_cosium, name="export_ca_cosium"),
        path("reset_clients_in_sales/", reset_clients_in_sales, name="reset_clients_in_sales"),
        path(
            "reset_exhange_rates_in_sales/",
            reset_exhange_rates_in_sales,
            name="reset_exhange_rates_in_sales",
        ),
        path("reset_sales/", reset_sales, name="reset_sales"),
        path("reset_ca/", reset_ca, name="reset_ca"),
    ]
)
