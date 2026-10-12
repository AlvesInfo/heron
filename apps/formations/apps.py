"""Configuration Django de l'application formations."""

from django.apps import AppConfig


class FormationsConfig(AppConfig):
    """Configuration de l'application formations."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.formations"
