"""Configuration Django de l'application rfa."""

from django.apps import AppConfig


class RfaConfig(AppConfig):
    """Configuration de l'application rfa."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.rfa"
