"""Configuration Django de l'application data_flux."""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Configuration de l'application data_flux."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.data_flux"
