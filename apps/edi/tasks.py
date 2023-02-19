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
from celery.exceptions import SoftTimeLimitExceeded, TimeLimitExceeded
from django.utils import timezone

from apps.edi.loggers import EDI_LOGGER
from apps.edi.loops.imports_loop_pool import main as edi_main
from apps.data_flux.trace import get_trace
from apps.edi.bin.edi_post_processing_pool import (
    bbgr_statment_post_insert,
    bbgr_monthly_post_insert,
    bbgr_retours_post_insert,
)
from apps.edi.bin.bbgr_002_statment import insert_bbgr_stament_file
from apps.edi.bin.bbgr_003_monthly import insert_bbgr_monthly_file
from apps.edi.bin.bbgr_004_retours import insert_bbgr_retours_file
from apps.edi.bin.bbgr_005_receptions import insert_bbgr_receptions_file
from apps.edi.imports.imports_suppliers_incoices_pool import (
    bbgr_bulk,
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
}


@shared_task
def start_edi_import():
    """Lancement de la tâche edi import"""
    try:
        edi_main()

    except (SoftTimeLimitExceeded, TimeLimitExceeded) as error:
        raise Exception from error


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


@shared_task
def bbgr_statment():
    """
    Insertion depuis B.I des factures BBGR Statment
    """
    trace_name = "Import BBGR Statment"
    application_name = "edi_imports_imports_suppliers_incoices"
    flow_name = "BbgrStatment"
    comment = ""
    trace = get_trace(
        trace_name,
        "insert into (...) selec ... from heron_bi_factures_billstatement",
        application_name,
        flow_name,
        comment,
    )
    error = False

    try:
        insert_bbgr_stament_file(uuid_identification=trace.uuid_identification)
    except Exception as except_error:
        error = True
        EDI_LOGGER.exception(f"Exception Générale : {except_error!r}")

    if error:
        trace.errors = True
        trace.comment = trace.comment + "\n. Une erreur c'est produite veuillez consulter les logs"

    to_print = f"Import : {flow_name}\n"
    bbgr_statment_post_insert(trace.uuid_identification)
    trace.time_to_process = (timezone.now() - trace.created_at).total_seconds()
    trace.final_at = timezone.now()
    trace.save()

    return {"import : ": f"{flow_name} - {trace.time_to_process} s"}


@shared_task
def bbgr_monthly():
    """
    Insertion depuis B.I des factures BBGR Monthly
    """
    trace_name = "Import BBGR Monthly"
    application_name = "edi_imports_imports_suppliers_incoices"
    flow_name = "BbgrMonthly"
    comment = ""
    trace = get_trace(
        trace_name,
        (
            "insert into (...) selec ... from heron_bi_factures_monthlydelivery "
            "where type_article not in ('FRAIS_RETOUR', 'DECOTE')"
        ),
        application_name,
        flow_name,
        comment,
    )
    error = False

    try:
        insert_bbgr_monthly_file(uuid_identification=trace.uuid_identification)
    except Exception as except_error:
        error = True
        EDI_LOGGER.exception(f"Exception Générale : {except_error!r}")

    if error:
        trace.errors = True
        trace.comment = trace.comment + "\n. Une erreur c'est produite veuillez consulter les logs"

    to_print = f"Import : {flow_name}\n"
    bbgr_monthly_post_insert(trace.uuid_identification)
    trace.time_to_process = (timezone.now() - trace.created_at).total_seconds()
    trace.final_at = timezone.now()
    trace.save()

    return {"import : ": f"{flow_name} - {trace.time_to_process} s"}


@shared_task
def bbgr_retours():
    """
    Insertion depuis B.I des factures Monthly Retours
    """
    trace_name = "Import BBGR Retours"
    application_name = "edi_imports_imports_suppliers_incoices"
    flow_name = "BbgrRetours"
    comment = ""
    trace = get_trace(
        trace_name,
        (
            "insert into (...) selec ... from heron_bi_factures_monthlydelivery "
            "where type_article in ('FRAIS_RETOUR', 'DECOTE')"
        ),
        application_name,
        flow_name,
        comment,
    )
    error = False

    try:
        insert_bbgr_retours_file(uuid_identification=trace.uuid_identification)
    except Exception as except_error:
        error = True
        EDI_LOGGER.exception(f"Exception Générale : {except_error!r}")

    if error:
        trace.errors = True
        trace.comment = trace.comment + "\n. Une erreur c'est produite veuillez consulter les logs"

    to_print = f"Import : {flow_name}\n"
    bbgr_retours_post_insert(trace.uuid_identification)
    trace.time_to_process = (timezone.now() - trace.created_at).total_seconds()
    trace.final_at = timezone.now()
    trace.save()

    return {"import : ": f"{flow_name} - {trace.time_to_process} s"}


@shared_task
def bbgr_receptions():
    """
    Insertion depuis B.I des factures BBGR Monthly
    """
    trace_name = "Import BBGR Receptions"
    application_name = "edi_imports_imports_suppliers_incoices"
    flow_name = "BbgrReceptions"
    comment = ""
    trace = get_trace(
        trace_name,
        "insert into (...) selec ... from heron_bi_receptions_bbgr ",
        application_name,
        flow_name,
        comment,
    )
    error = False

    try:
        insert_bbgr_receptions_file(uuid_identification=trace.uuid_identification)
    except Exception as except_error:
        error = True
        EDI_LOGGER.exception(f"Exception Générale : {except_error!r}")

    if error:
        trace.errors = True
        trace.comment = trace.comment + "\n. Une erreur c'est produite veuillez consulter les logs"

    to_print = f"Import : {flow_name}\n"
    bbgr_retours_post_insert(trace.uuid_identification)
    trace.time_to_process = (timezone.now() - trace.created_at).total_seconds()
    trace.final_at = timezone.now()
    trace.save()

    return {"import : ": f"{flow_name} - {trace.time_to_process} s"}
