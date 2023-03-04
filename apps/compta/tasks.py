# pylint: disable=E0401,W0703,W1201,W1203
"""
FR : Module de génération des Roylaties, Pubicités et Prestations sous task Celery
EN : Module for generating Roylaties, Advertisements and Services under task Celery

Commentaire:

created at: 2023-03-03
created by: Paulo ALVES

modified at: 2023-03-03
modified by: Paulo ALVES
"""
from typing import AnyStr
import time

from celery import shared_task

from apps.edi.loggers import EDI_LOGGER
from apps.users.models import User
from apps.parameters.bin.core import get_object


@shared_task(name="subscription_launch_task")
def subscription_launch_task(task_to_launch: AnyStr, dte_d: AnyStr, dte_f: AnyStr, user: User):
    """Lancement de la génération des Royalties
    :param task_to_launch: Tâche à lancer
    :param dte_d: Date de début de période au format texte isoformat
    :param dte_f: Date de fin de période au format texte isoformat
    :param user: Utilisateur lançant la génération
    :return:
    """
    start_initial = time.time()

    error = False
    trace = None
    to_print = ""
    function = get_object(task_to_launch)

    try:
        trace, to_print = function(dte_d, dte_f)
        trace.created_by = user
    except TypeError as except_error:
        error = True
        to_print += f"TypeError : {except_error}\n"
        EDI_LOGGER.exception(f"TypeError : {except_error!r}")

    except Exception as except_error:
        error = True
        EDI_LOGGER.exception(f"Exception Générale: {task_to_launch}\n{except_error!r}")

    finally:
        if error and trace:
            trace.errors = True
            trace.comment = (
                trace.comment + "\n. Une erreur c'est produite veuillez consulter les logs"
            )

        if trace is not None:
            trace.save()

    EDI_LOGGER.warning(
        to_print
        + f"Génération des abonnement - {task_to_launch} : {time.time() - start_initial} s"
        + "\n\n======================================================================="
        "======================================================================="
    )

    return {"Génération des abonnement : ": f" {task_to_launch} - {trace.time_to_process} s"}
