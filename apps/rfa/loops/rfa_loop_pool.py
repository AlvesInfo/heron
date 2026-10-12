"""FR : Module d'import en boucle des fichiers de factures fournisseurs.

EN : Loop import module for invoices suppliers files.

Commentaire:

created at: 2022-04-09
created by: Paulo ALVES

modified at: 2022-04-09
modified by: Paulo ALVES
"""

import time
from typing import Any

from celery import group

from apps.parameters.bin.core import get_action
from heron import celery_app
from heron.loggers import LOGGER_EDI, LOGGER_IMPORT


def rfa_generation_launch(user_pk: int, suppliers_list: list, period_rfa: str):
    """Main pour lancement de la génération des RFA."""
    active_action = None
    result: Any = ""

    try:
        # On attend qu'aucune génération ne soit en cours
        active_action = get_action(action="rfa_generation")

        while active_action.in_progress:
            active_action = get_action(action="rfa_generation")

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

        LOGGER_IMPORT.info("%s %s", "result : ", result)
        LOGGER_EDI.warning("result : %r,\nin %s s", result, time.time() - start_all)

        result_clean = group(
            *[celery_app.signature("sql_clean_general", kwargs={"start_all": start_all})]
        )().get(3600)

        LOGGER_IMPORT.info("%s %s", "result_clean : ", result_clean)
        LOGGER_EDI.warning("result_clean : %r,\nin %s s", result_clean, time.time() - start_all)

    except Exception:
        LOGGER_EDI.exception(
            "Erreur détectée dans apps.rfa.loops.rfa_loop_pool.celery_rfa_generation_launch()"
        )

    finally:
        # On remet l'action en cours à False, après l'execution
        if active_action is not None:
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
