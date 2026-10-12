"""Configuration Django de l'application parameters."""

from django.apps import AppConfig


class ParametersConfig(AppConfig):
    """Configuration de l'application parameters."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.parameters"
