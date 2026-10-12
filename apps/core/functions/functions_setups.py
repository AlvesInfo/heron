"""Module de setup."""

import os
import platform
import sys

import django
from django.db import connection, connections, transaction
from django.db.utils import IntegrityError


# Configuration Django
def setup_django():
    """Initialise Django pour un script autonome selon le système d'exploitation."""
    base_dir = r"C:\\SitesWeb\\heron"

    if platform.system() == "Darwin":
        base_dir = "/Users/paulo/SitesWeb/heron"
    elif platform.system() == "Linux":
        base_dir = "/home/paulo/heron"

    sys.path.insert(0, base_dir)
    sys.path.append(base_dir)

    # Configurer Django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")

    # Initialiser Django une seule fois
    try:
        django.setup()
    except RuntimeError as e:
        if "populate() isn't reentrant" not in str(e):
            raise


# Appeler au début du script
setup_django()

from django.conf import settings

from apps.users.models import User

CNX_STRING = settings.CNX_STRING

# Ré-exports : les scripts importent ces objets Django une fois le setup réalisé
__all__ = [
    "CNX_STRING",
    "IntegrityError",
    "User",
    "connection",
    "connections",
    "settings",
    "transaction",
]
