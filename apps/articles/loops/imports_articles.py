# pylint: disable=E0401,C0413
"""
FR : Module de lancement de la boucle d'import des articles Acuitis
EN : Module for launching the articles Acuitis import loop by supervisor

Commentaire:

created at: 2022-12-31
created by: Paulo ALVES

modified at: 2022-12-31
modified by: Paulo ALVES
"""
import os
import platform
import sys
from datetime import datetime
import time

import django

BASE_DIR = r"/"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")
django.setup()

from heron.loggers import LOGGER_EDI
from apps.articles.bin.bbgr_002_articles import insert_bbgr_002_articles
from apps.articles.bin.bbgr_003_articles import insert_bbgr_003_articles
from apps.articles.bin.bbgr_004_articles import insert_bbgr_004_articles


def main():
    """Main Function"""
    try:
        insert_bbgr_002_articles()
    except Exception as except_error:
        LOGGER_EDI.exception(
            f"Exception Générale: sur fonction insert_bbgr_002_articles()\n{except_error!r}"
        )

    try:
        insert_bbgr_003_articles()
    except Exception as except_error:
        LOGGER_EDI.exception(
            f"Exception Générale: sur fonction insert_bbgr_003_articles()\n{except_error!r}"
        )

    try:
        insert_bbgr_004_articles()
    except Exception as except_error:
        LOGGER_EDI.exception(
            f"Exception Générale: sur fonction insert_bbgr_004_articles()\n{except_error!r}"
        )


if __name__ == "__main__":
    while True:
        maintenant = datetime.now()
        heure = maintenant.hour
        minute = maintenant.minute

        if heure == 9 and minute == 30:
            print("lancement import articles Acuitis : ", maintenant)
            main()

        time.sleep(60)
