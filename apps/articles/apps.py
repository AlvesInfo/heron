"""Configuration Django de l'application articles."""

from django.apps import AppConfig


class ArticlesConfig(AppConfig):
    """Configuration de l'application articles."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.articles"
