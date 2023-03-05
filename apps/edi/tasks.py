# pylint: disable=C0303,E0401,W1203,W0703,R0912,R0913,R0914,R0915,W1201
"""
FR : Module d'import des factures founisseurs EDI sous task Celery
EN : Import module for EDI incoives suppliers by celery tasks

Commentaire:

created at: 2022-04-08
created by: Paulo ALVES

modified at: 2023-02-23
modified by: Paulo ALVES
"""
import shutil
from pathlib import Path
from typing import AnyStr
import time
from uuid import UUID

from celery import shared_task

from apps.edi.loggers import EDI_LOGGER

from apps.edi.imports.imports_suppliers_incoices_pool import (
    bbgr_bulk,
    bbgr_statment,
    bbgr_monthly,
    bbgr_retours,
    bbgr_receptions,
    cosium,
    transfert_cosium,
    edi,
    eye_confort,
    generique,
    hearing,
    interson,
    johnson,
    lmc,
    newson,
    phonak,
    prodition,
    signia,
    starkey,
    technidis,
    unitron,
    widex,
    widex_ga,
    z_bu_refac,
)
from apps.edi.bin.edi_post_processing_pool import post_common
from apps.edi.bin.edi_post_processing_pool import post_processing_all
from apps.users.models import User
from apps.parameters.bin.core import get_object

processing_dict = {
    "BBGR_BULK": bbgr_bulk,
    "COSIUM": cosium,
    "EDI": edi,
    "EYE_CONFORT": eye_confort,
    "GENERIQUE": generique,
    "HEARING": hearing,
    "INTERSON": interson,
    "JOHNSON": johnson,
    "LMC": lmc,
    "NEWSON": newson,
    "PHONAK": phonak,
    "PRODITION": prodition,
    "SIGNIA": signia,
    "STARKEY": starkey,
    "TECHNIDIS": technidis,
    "TRANSFERTS": transfert_cosium,
    "UNITRON": unitron,
    "WIDEX": widex,
    "WIDEX_GA": widex_ga,
    "SAGE_YOOZ_REFAC0": z_bu_refac,
}

bbgr_dict = {
    "bbgr_statment": bbgr_statment,
    "bbgr_monthly": bbgr_monthly,
    "bbgr_retours": bbgr_retours,
    "bbgr_receptions": bbgr_receptions,
}


@shared_task(name="suppliers_import")
def launch_suppliers_import(process_objects, user_pk):
    """
    Intégration des factures fournisseurs présentes
    dans le répertoire de processing/suppliers_invoices_files
    """

    start_initial = time.time()

    error = False
    trace = None
    to_print = ""
    str_file, str_backup_file, processing_key = process_objects
    file = Path(str_file)
    backup_file = Path(str_backup_file)
    function = processing_dict.get(processing_key)

    try:
        user = User.objects.get(pk=user_pk)
        trace, to_print = function(file)
        trace.created_by = user
    except TypeError as except_error:
        error = True
        to_print += f"TypeError : {except_error}\n"
        EDI_LOGGER.exception(f"TypeError : {except_error!r}")

    except Exception as except_error:
        error = True
        EDI_LOGGER.exception(f"Exception Générale: {file.name}\n{except_error!r}")

    finally:
        if error and trace:
            trace.errors = True
            trace.comment = (
                trace.comment + "\n. Une erreur c'est produite veuillez consulter les logs"
            )

        if trace is not None:
            trace.save()

        if file.is_file() and not backup_file.is_file():
            shutil.move(file.resolve(), backup_file.resolve())
        elif file.is_file():
            file.unlink()

        # TODO : faire une fonction d'envoie de mails

    EDI_LOGGER.warning(
        to_print
        + f"Validation {file.name} in : {time.time() - start_initial} s"
        + "\n\n======================================================================="
        "======================================================================="
    )

    return {"import : ": f"edi - {processing_key} - {trace.time_to_process} s"}


@shared_task(name="bbgr_bi")
def launch_bbgr_bi_import(function_name, user_pk):
    """
    Intégration des factures fournisseurs présentes
    dans le répertoire de processing/suppliers_invoices_files
    """

    start_initial = time.time()

    error = False
    trace = None
    to_print = ""
    function = bbgr_dict.get(function_name)

    try:
        user = User.objects.get(pk=user_pk)
        trace, to_print = function()
        trace.created_by = user

    except TypeError as except_error:
        error = True
        to_print += f"TypeError : {except_error}\n"
        EDI_LOGGER.exception(f"TypeError : {except_error!r}")

    except Exception as except_error:
        error = True
        EDI_LOGGER.exception(f"Exception Générale: {function_name}\n{except_error!r}")

    finally:
        if error and trace:
            trace.errors = True
            trace.comment = (
                trace.comment + "\n. Une erreur c'est produite veuillez consulter les logs"
            )

        if trace is not None:
            trace.save()

        # TODO : faire une fonction d'envoie de mails

    EDI_LOGGER.warning(
        to_print
        + f"Validation {function_name} in : {time.time() - start_initial} s"
        + "\n\n======================================================================="
        "======================================================================="
    )

    return {"import : ": f"BBGR BI - {function_name} - {trace.time_to_process} s"}


@shared_task(name="sql_clean_general")
def launch_sql_clean_general(start_all):
    """Realise les requêtes sql générale, pour le néttoyages des imports"""
    start_initial = time.time()

    try:
        post_common()
        print("post_common terminé")
        EDI_LOGGER.warning("post_common terminé")

        post_processing_all()
        print("post_processing_all terminé")
        EDI_LOGGER.warning("post_processing_all terminé")

        print(f"All validations : {time.time() - start_all} s")
        EDI_LOGGER.warning(f"All validations : {time.time() - start_all} s")

    except Exception as except_error:
        EDI_LOGGER.exception(
            f"Exception Générale: sur tâche launch_sql_clean_general\n{except_error!r}"
        )

    return {
        "Clean Sql Général : ": f"{time.time() - start_initial} s",
        "Ensemble": f"All validations : {time.time() - start_all} s",
    }


@shared_task(name="subscription_launch_task")
def subscription_launch_task(task_to_launch: AnyStr, dte_d: AnyStr, dte_f: AnyStr, user: UUID):
    """Génération des Roylaties, Pubicités et Prestations sous task Celery
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
    print(function.__name__)
    try:
        trace, to_print = function(dte_d, dte_f, user)
        trace.created_by = User.objects.get(uuid_identification=UUID(user))
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
