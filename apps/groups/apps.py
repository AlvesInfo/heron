"""Configuration Django de l'application groups."""

from django.apps import AppConfig


class GroupsConfig(AppConfig):
    """Configuration de l'application groups."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.groups"
