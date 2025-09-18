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

from typing import AnyStr
import time

from celery import shared_task
from django.utils import timezone

from heron.loggers import LOGGER_EDI
from apps.data_flux.trace import get_trace
from apps.users.models import User
from apps.rfa.imports.import_rfa_pool import generate_rfa


@shared_task(name="rfa_generation_launch_task")
def launch_rfa_generation(user_pk: int, supplier_origin: AnyStr, period_rfa: AnyStr):
    """
    Génération des RFA mensuelles
    """

    start_initial = time.time()

    error = False

    trace_name = "Génération des RFA Mensuelles"
    application_name = "edi_imports_suppliers_invoices_pool"
    flow_name = "rfa_flow"
    comment = ""
    trace = get_trace(
        trace_name,
        f"Generate RFA : {supplier_origin}",
        application_name,
        flow_name,
        comment,
    )
    to_print = ""
    user = User.objects.get(pk=user_pk)
    trace.created_by = user

    try:
        to_print = generate_rfa(supplier_origin, period_rfa, trace)

    except TypeError as except_error:
        error = True
        to_print += f"TypeError : {except_error}\n"
        LOGGER_EDI.exception(f"TypeError : {except_error!r}")

    except Exception as except_error:
        error = True
        LOGGER_EDI.exception(
            f"Exception Générale RFA: {supplier_origin}\n{except_error!r}"
        )

    finally:
        if error and trace:
            trace.errors = True
            trace.comment = (
                trace.comment
                + "\n. Error: Une erreur c'est produite veuillez consulter les logs"
            )

        if trace is not None:
            trace.time_to_process = (timezone.now() - trace.created_at).total_seconds()
            trace.final_at = timezone.now()
            trace.invoices = True
            trace.save()

    LOGGER_EDI.warning(
        to_print
        + f"Validation RFA : {supplier_origin} in : {time.time() - start_initial} s"
        + "\n\n======================================================================="
        "======================================================================="
    )
    sep = ":" if trace.comment else ""

    if not error and "Erreur" not in to_print:
        return {
            "Génération des RFA": f"RFA intégrées avec sucess, en {trace.time_to_process} s"
        }

    return {
        "Génération des RFA": (
            f"Erreur - {to_print.replace('Erreur', '')} {sep} {trace.comment!r}"
        )
    }
