# pylint: disable=E0401,E0402,W0703,W1203,C0413,C0303,W1201,E1101,C0415,E0611,W0511
# ruff: noqa: E402
"""
FR : Module d'import en boucle des fichiers de factures fournisseurs
EN : Loop import module for invoices suppliers files

Commentaire:

created at: 2022-04-09
created by: Paulo ALVES

modified at: 2022-04-09
modified by: Paulo ALVES
"""

from typing import AnyStr, List
import os
import platform
import sys
import time

import django

BASE_DIR = r"C:\SitesWeb\heron"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")

django.setup()

from celery import group

from heron import celery_app
from heron.loggers import LOGGER_EDI
from apps.parameters.bin.core import get_action


def rfa_generation_launch(user_pk: int, suppliers_list: List, period_rfa: AnyStr):
    """Main pour lancement de la génération des RFA"""

    active_action = None
    result = ""
    action = True

    try:
        while action:
            active_action = get_action(action="rfa_generation")
            if not active_action.in_progress:
                action = False

        start_all = time.time()

        # On initialise l'action comme en cours
        active_action.in_progress = True
        active_action.save()

        # On regroupe les tâches celery à lancer pour tous les fournisseurs
        result = group(
            *[
                celery_app.signature(
                    "rfa_generation_launch_task",
                    kwargs={
                        "user_pk": user_pk,
                        "supplier_origin": supplier,
                        "period_rfa": period_rfa,
                    },
                )
                for supplier in suppliers_list
            ]
        )().get(3600)

        print("result : ", result)
        LOGGER_EDI.warning(f"result : {result!r},\nin {time.time() - start_all} s")

        result_clean = group(
            *[
                celery_app.signature(
                    "sql_clean_general", kwargs={"start_all": start_all}
                )
            ]
        )().get(3600)

        print("result_clean : ", result_clean)
        LOGGER_EDI.warning(
            f"result_clean : {result_clean!r},\nin {time.time() - start_all} s"
        )

    except Exception as error:
        print("Error : ", error)
        LOGGER_EDI.exception(
            "Erreur détectée dans apps.rfa.loops.rfa_loop_pool.celery_rfa_generation_launch()"
        )

    finally:
        # On remet l'action en cours à False, après l'execution
        active_action.in_progress = False
        active_action.save()

    if isinstance(result, (list,)) and result:
        result = result[0]

    info = (
        result.replace(r"\n", "")
        if isinstance(result, (str,))
        else ". ".join(list(result.values())).replace(r"\n", "")
    )
    return "Erreur" in info, info
