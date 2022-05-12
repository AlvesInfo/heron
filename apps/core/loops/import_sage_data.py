# pylint: disable=E0401,C0413
"""
FR : Module de lancement de la boucle d'import des fichiers sage par supervisor
EN : Module for launching the sage file import loop by supervisor

Commentaire:

created at: 2022-05-11
created by: Paulo ALVES

modified at: 2022-05-11
modified by: Paulo ALVES
"""
import os
import platform
import sys
from datetime import datetime
import time

import django

BASE_DIR = r"C:\SitesWeb\heron"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")
django.setup()

from apps.countries.loops.imports_loop import process as process_countries
from apps.accountancy.loops.imports_loop import process as process_accountancy
from apps.book.loops.imports_loop import process as process_book


if __name__ == "__main__":
    while True:
        maintenant = datetime.now()
        heure = maintenant.hour
        minute = maintenant.minute

        if heure == 6 and minute == 30:
            print("lancement import sage : ", maintenant)
            process_countries()
            process_accountancy()
            process_book()

        time.sleep(60)
