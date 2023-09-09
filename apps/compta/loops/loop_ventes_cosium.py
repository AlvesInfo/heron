# pylint: disable=W0703,W1203,E0401
"""
FR : Module d'import en boucle des ventes cosium
EN : Cosium sales loop import module

Commentaire:

created at: 2023-03-02
created by: Paulo ALVES

modified at: 2023-03-02
modified by: Paulo ALVES
"""
import os
import platform
import sys
import time

import django

BASE_DIR = r"/"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")

django.setup()

import pendulum

from heron.loggers import LOGGER_IMPORT
from apps.data_flux.models import Trace
from apps.compta.imports.import_ventes_cosium import insert_ventes_cosium, mise_a_jour_ventes_cosium


def process():
    """
    Intégration des fichiers en fonction des fichiers présents dans le répertoire de processing/sage
    """
    start = time.time()
    error = False
    trace = Trace(
        trace_name="Import Ventes Cosium",
        file_name="insert into (...) select ... from heron_bi_ventes_cosium",
        application_name="insert_ventes_cosium",
        flow_name="VentesCosium",
        comment="Import journalier des ventes Cosium depuis la B.I.",
        created_numbers_records=0,
        updated_numbers_records=0,
        errors_numbers_records=0,
        unknown_numbers_records=0,
    )
    trace.save()
    try:
        insert_ventes_cosium()

        day = pendulum.now().day

        if day in {1, 2, 3, 4, 5, 6}:
            mise_a_jour_ventes_cosium()

    except TypeError as except_error:
        error = True
        LOGGER_IMPORT.exception(f"TypeError : Import Ventes Cosium\n{except_error!r}")

    except Exception as except_error:
        error = True
        LOGGER_IMPORT.exception(f"Exception Générale: Import Ventes Cosium\n{except_error!r}")

    finally:
        if error and trace:
            trace.errors = True
            trace.comment = (
                trace.comment + "\n. Une erreur c'est produite veuillez consulter les logs"
            )

        if trace is not None:
            trace.time_to_process = time.time() - start
            trace.final_at = pendulum.now()
            trace.save()


if __name__ == "__main__":
    while True:
        maintenant = pendulum.now()
        heure = maintenant.hour
        minute = maintenant.minute

        if heure == 10 and minute == 00:
            print(f"[{maintenant}] : lancement import ventes Cosium")
            process()

        time.sleep(60)
