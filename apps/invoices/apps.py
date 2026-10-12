"""Configuration Django de l'application invoices."""

from django.apps import AppConfig


class SuppliersInvoicesConfig(AppConfig):
    """Configuration de l'application invoices."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.invoices"
