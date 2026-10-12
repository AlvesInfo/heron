"""Configuration Django de l'application edi."""

from django.apps import AppConfig


class EdiConfig(AppConfig):
    """Configuration de l'application edi."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.edi"
