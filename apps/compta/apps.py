"""Configuration Django de l'application compta."""

from django.apps import AppConfig


class ComptaConfig(AppConfig):
    """Configuration de l'application compta."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.compta"
