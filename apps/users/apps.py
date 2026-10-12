"""Configuration Django de l'application users."""

from django.apps import AppConfig


class UsersConfig(AppConfig):
    """Configuration de l'application users."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.users"
