"""Configuration Django de l'application countries."""

from django.apps import AppConfig


class CountriesConfig(AppConfig):
    """Configuration de l'application countries."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.countries"
