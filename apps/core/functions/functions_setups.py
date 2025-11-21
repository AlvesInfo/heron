"""
Module de setup
"""

import os
import sys
import platform

import django

from django.db import connection, connections, transaction
from django.db.utils import IntegrityError


# Configuration Django
def setup_django():
    BASE_DIR = r"C:\\SitesWeb\\heron"

    if platform.system() == "Darwin":
        BASE_DIR = "/Users/paulo/SitesWeb/heron"
    elif platform.system() == "Linux":
        BASE_DIR = "/home/paulo/heron"

    sys.path.insert(0, BASE_DIR)
    sys.path.append(BASE_DIR)

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

import heron.settings as settings
from apps.users.models import User

settings = settings
connection = connection
connections = connections
transaction = transaction
IntegrityError = IntegrityError
CNX_STRING = settings.CNX_STRING
User = User
