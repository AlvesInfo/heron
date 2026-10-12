"""Configuration Django de l'application od."""

from django.apps import AppConfig


class OdConfig(AppConfig):
    """Configuration de l'application od."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.od"
