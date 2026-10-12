"""Configuration Django de l'application traces."""

from django.apps import AppConfig


class TracesConfig(AppConfig):
    """Configuration de l'application traces."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.traces"
