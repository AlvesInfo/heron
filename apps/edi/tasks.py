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
import time
import shutil
from pathlib import Path

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
def launch_suppliers_import(process_objects):
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
        trace, to_print = function(file)

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
def launch_bbgr_bi_import(function_name):
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
        trace, to_print = function()

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
