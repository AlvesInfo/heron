"""Configuration Django de l'application book."""

from django.apps import AppConfig


class SuppliersBookConfig(AppConfig):
    """Configuration de l'application book."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.book"
