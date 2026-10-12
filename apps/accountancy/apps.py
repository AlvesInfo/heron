"""Configuration Django de l'application accountancy."""

from django.apps import AppConfig


class AccountancyConfig(AppConfig):
    """Configuration de l'application accountancy."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accountancy"
