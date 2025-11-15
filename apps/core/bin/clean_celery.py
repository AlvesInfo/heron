from functools import wraps
import gc
from django.db import reset_queries


def clean_memory(func):
    """clean memory for celery task"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            # Réinitialiser les requêtes Django
            reset_queries()
            # Forcer le garbage collector
            gc.collect()

    return wrapper
