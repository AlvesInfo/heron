"""
Module de setup
"""
import os
import sys
import platform

import django
from django.db import connection, connections
from django.db.utils import IntegrityError

BASE_DIR = r"D:\SitesWeb\heron"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/palves/heron"

sys.path.insert(0, BASE_DIR)
sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")
django.setup()

import heron.settings as settings

settings = settings
connection = connection
connections = connections
IntegrityError = IntegrityError
