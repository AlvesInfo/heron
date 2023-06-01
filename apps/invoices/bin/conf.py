# pylint: disable=E0401
"""
FR : Elements de configuration du Module de génération des factures de Formations en pdf
EN : Configuration Elements of Module for generating invoices Formations in pdf

Commentaire:

created at: 2023-06-01
created by: Paulo ALVES

modified at: 2023-06-01
modified by: Paulo ALVES
"""
import os
import sys
import platform

import django

BASE_DIR = r"/"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")

django.setup()

DOMAIN = "http://10.9.2.109" if BASE_DIR == "/home/paulo/heron" else "http://127.0.0.1:8000"