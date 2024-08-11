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

from apps.data_flux.trace import Trace
from apps.rfa.bin.rfa_post_insert import rfa_post_upadte
from apps.rfa.bin.rfa_insertions import insert_rfa


def generate_rfa(supplier_origin: AnyStr, period_rfa: AnyStr, trace: Trace):
    """Génération mensuelle des RFA"""

    nb_insert = insert_rfa(
        supplier_origin, period_rfa, uuid_identification=trace.uuid_identification
    )

    trace.created_numbers_records = nb_insert
    trace.save()

    rfa_post_upadte(trace.uuid_identification)

    to_print = f"Import : {trace.flow_name}\n"

    return to_print
