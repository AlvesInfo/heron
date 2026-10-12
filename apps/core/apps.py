"""Configuration Django de l'application core."""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Configuration de l'application core."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
