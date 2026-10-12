"""FR : Module de lancement de la boucle d'import des articles Acuitis par supervisor.

EN : Module for launching the articles Acuitis import loop by supervisor.

Commentaire:

created at: 2022-12-31
created by: Paulo ALVES

modified at: 2022-12-31
modified by: Paulo ALVES
"""

import os
import platform
import sys
import time

import django
from django.utils import timezone

BASE_DIR = r"/"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")

django.setup()

from apps.articles.bin.bbgr_002_articles import insert_bbgr_002_articles
from apps.articles.bin.bbgr_003_articles import insert_bbgr_003_articles
from apps.articles.bin.bbgr_004_articles import insert_bbgr_004_articles
from apps.articles.bin.bbgr_006_articles import insert_bbgr_006_articles
from heron.loggers import LOGGER_EDI


def main():
    """Main Function."""
    try:
        insert_bbgr_002_articles()
    except Exception:
        LOGGER_EDI.exception("Exception Générale: sur fonction insert_bbgr_002_articles()")

    try:
        insert_bbgr_003_articles()
    except Exception:
        LOGGER_EDI.exception("Exception Générale: sur fonction insert_bbgr_003_articles()")

    try:
        insert_bbgr_004_articles()
    except Exception:
        LOGGER_EDI.exception("Exception Générale: sur fonction insert_bbgr_004_articles()")

    try:
        insert_bbgr_006_articles()
    except Exception:
        LOGGER_EDI.exception("Exception Générale: sur fonction insert_bbgr_006_articles()")


if __name__ == "__main__":
    while True:
        maintenant = timezone.localtime()
        heure = maintenant.hour
        minute = maintenant.minute

        if heure == 9 and minute == 30:
            print(f"[{maintenant}] : lancement import articles Acuitis")
            main()

        time.sleep(60)
