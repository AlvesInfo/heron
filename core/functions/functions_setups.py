"""
Module de setup
"""
import os
import sys
import platform

import django
from django.db import connection, connections

BASE_DIR = "D:\SitesWeb\heron"

if platform.uname().node == "PauloMSI":
    sys.path.insert(0, BASE_DIR)
    sys.path.append(BASE_DIR)
else:
    BASE_DIR = "/home/palves/heron"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")
django.setup()

import heron.settings as settings

connection = connection
connections = connections
