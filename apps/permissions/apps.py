"""Configuration Django de l'application permissions."""

from django.apps import AppConfig


class PermissionsConfig(AppConfig):
    """Configuration de l'application permissions."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.permissions"
