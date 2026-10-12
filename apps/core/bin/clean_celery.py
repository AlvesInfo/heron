"""Décorateur de nettoyage mémoire pour les tâches Celery."""

import gc
from functools import wraps

from django.db import reset_queries


def clean_memory(func):
    """Clean memory for celery task."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        finally:
            # Réinitialiser les requêtes Django
            reset_queries()
            # Forcer le garbage collector
            gc.collect()

    return wrapper
