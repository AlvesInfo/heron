# pylint: disable=E0401
"""
FR : Module de génération des RFA sous task Celery
EN : RFA generation module under Celery task

Commentaire:

created at: 2024-09-09
created by: Paulo ALVES

modified at: 2024-09-09
modified by: Paulo ALVES
"""
import shutil
from pathlib import Path
from typing import AnyStr
import time
from uuid import UUID

from celery import shared_task

from heron.loggers import LOGGER_EDI
from apps.edi.imports.imports_suppliers_invoices_pool import (
    bbgr_bulk,
    bbgr_statment,
    bbgr_monthly,
    bbgr_retours,
    bbgr_receptions,
    cosium,
    cosium_achats,
    transfert_cosium,
    edi,
    eye_confort,
    generique,
    generique_internal,
    hansaton,
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
from apps.edi.bin.edi_post_processing_pool import (
    post_vacuum,
    post_processing_all,
    edi_trace_supplier_insert,
)
from apps.edi.bin.exclusions import set_exclusions
from apps.users.models import User
from apps.parameters.bin.core import get_object
from apps.rfa.imports.import_rfa_pool import generate_rfa


@shared_task(name="rfa_generation_launch_task")
def launch_rfa_generation(user_pk, supplier_origin, period_rfa):
    """
    Génération des RFA mensuelles
    """

    start_initial = time.time()

    error = False
    trace = None
    to_print = ""

    try:
        user = User.objects.get(pk=user_pk)
        trace, to_print = generate_rfa(supplier_origin, period_rfa)
        trace.created_by = user
    except TypeError as except_error:
        error = True
        to_print += f"TypeError : {except_error}\n"
        LOGGER_EDI.exception(f"TypeError : {except_error!r}")

    except Exception as except_error:
        error = True
        LOGGER_EDI.exception(f"Exception Générale RFA: {supplier_origin}\n{except_error!r}")

    finally:
        if error and trace:
            trace.errors = True
            trace.comment = (
                trace.comment + "\n. Une erreur c'est produite veuillez consulter les logs"
            )

        if trace is not None:
            trace.invoices = True
            trace.save()

    LOGGER_EDI.warning(
        to_print
        + f"Validation RFA : {supplier_origin} in : {time.time() - start_initial} s"
        + "\n\n======================================================================="
        "======================================================================="
    )

    return {"import : ": f"RFA - {supplier} - {time.time() - start_initial} s"}

