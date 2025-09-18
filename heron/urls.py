"""heron URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from heron.views import home, reactivate, logout_email


urlpatterns = [
    path("back-heron-plateforme/", admin.site.urls),
    path("", home, name="home"),
    # Gestion du login et du reset des password ====================================================
    *[
        path("accounts/", include(("apps.users.urls", "apps.users"), namespace="accounts")),
        path("logout_email/", logout_email, name="logout_email"),
        path(
            "password-reset/",
            PasswordResetView.as_view(
                template_name="heron/password_reset.html",
                email_template_name="heron/password_reset_email.html",
                subject_template_name="heron/password_reset_subject.txt",
            ),
            name="password_reset",
        ),
        path(
            "password-reset-done/",
            PasswordResetDoneView.as_view(template_name="heron/password_reset_done.html"),
            name="password_reset_done",
        ),
        path(
            "password-reset-confirm/<uidb64>/<token>/",
            PasswordResetConfirmView.as_view(template_name="heron/password_reset_confirm.html"),
            name="password_reset_confirm",
        ),
        path(
            "password-reset-complete/",
            PasswordResetCompleteView.as_view(template_name="heron/password_reset_complete.html"),
            name="password_reset_complete",
        ),
        path("reactivate/<uidb64>/<token>/", reactivate, name="reactivate"),
    ],
    # Applications =================================================================================
    *[
        path(
            "articles/",
            include(("apps.articles.urls", "apps.articles"), namespace="articles"),
        ),
        path("book/", include(("apps.book.urls", "apps.book"), namespace="book")),
        path(
            "centers_clients/",
            include(
                ("apps.centers_clients.urls", "apps.centers_clients"),
                namespace="centers_clients",
            ),
        ),
        path(
            "compta/",
            include(
                ("apps.compta.urls", "apps.compta"),
                namespace="compta",
            ),
        ),
        path(
            "centers_purchasing/",
            include(
                ("apps.centers_purchasing.urls", "apps.centers_purchasing"),
                namespace="centers_purchasing",
            ),
        ),
        path(
            "core/",
            include(("apps.core.urls", "apps.core"), namespace="core"),
        ),
        path(
            "countries/",
            include(("apps.countries.urls", "apps.countries"), namespace="countries"),
        ),
        path(
            "edi/",
            include(("apps.edi.urls", "apps.edi"), namespace="edi"),
        ),
        path(
            "groups/",
            include(("apps.groups.urls", "apps.groups"), namespace="groups"),
        ),
        path(
            "import_files/",
            include(("apps.import_files.urls", "apps.import_files"), namespace="import_files"),
        ),
        path(
            "parameters/",
            include(("apps.parameters.urls", "apps.parameters"), namespace="parameters"),
        ),
        path(
            "periods/",
            include(("apps.periods.urls", "apps.periods"), namespace="periods"),
        ),
        path(
            "permissions/",
            include(("apps.permissions.urls", "apps.permissions"), namespace="permissions"),
        ),
        path(
            "invoices/",
            include(
                ("apps.invoices.urls", "apps.invoices"),
                namespace="invoices",
            ),
        ),
        path(
            "traces/",
            include(
                ("apps.traces.urls", "apps.traces"),
                namespace="traces",
            ),
        ),
        path(
            "",
            include(("apps.users.urls", "apps.users"), namespace="users"),
        ),
        path(
            "validation_purchases/",
            include(
                ("apps.validation_purchases.urls", "apps.validation_purchases"),
                namespace="validation_purchases",
            ),
        ),
        path(
            "validation_sales/",
            include(
                ("apps.validation_sales.urls", "apps.validation_sales"),
                namespace="validation_sales",
            ),
        ),
        path(
            "data_flux/",
            include(
                ("apps.data_flux.urls", "apps.data_flux"),
                namespace="data_flux",
            ),
        ),
        path(
            "rfa/",
            include(
                ("apps.rfa.urls", "apps.rfa"),
                namespace="rfa",
            ),
        ),
    ],
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if settings.DEBUG:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]
