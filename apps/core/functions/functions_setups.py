"""
Module de setup
"""
import os
import sys
import platform

import django

BASE_DIR = r"C:\SitesWeb\heron"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.insert(0, BASE_DIR)
sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")

django.setup()

from django.db import connection, connections, transaction
from django.db.utils import IntegrityError

import heron.settings as settings

settings = settings
connection = connection
connections = connections
transaction = transaction
IntegrityError = IntegrityError
CNX_STRING = settings.CNX_STRING
