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

from django.utils import timezone

from heron.loggers import LOGGER_EDI
from apps.data_flux.trace import get_trace
from apps.rfa.bin.rfa_post_insert import rfa_post_upadte
from apps.rfa.bin.rfa_insertions import insert_rfa


def generate_rfa(supplier_origin: AnyStr, period_rfa: AnyStr):
    """Import du fichier des factures Cosium"""
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

    nb_insert = insert_rfa(
        supplier_origin, period_rfa, uuid_identification=trace.uuid_identification
    )

    trace.created_numbers_records = nb_insert
    trace.save()

    rfa_post_upadte(trace.uuid_identification)

    to_print = f"Import : {flow_name}\n"

    return trace, to_print

