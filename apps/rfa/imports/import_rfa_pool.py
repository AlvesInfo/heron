"""FR : Module de génération des RFA sous task Celery.

EN : RFA generation module under Celery task.

Commentaire:

created at: 2024-09-09
created by: Paulo ALVES

modified at: 2024-09-09
modified by: Paulo ALVES
"""

from apps.data_flux.trace import Trace
from apps.rfa.bin.rfa_insertions import insert_rfa
from apps.rfa.bin.rfa_post_insert import rfa_post_update


def generate_rfa(supplier_origin: str, period_rfa: str, trace: Trace):
    """Génération mensuelle des RFA."""
    nb_insert = insert_rfa(
        supplier_origin, period_rfa, uuid_identification=trace.uuid_identification
    )

    trace.created_numbers_records = nb_insert
    trace.save()

    rfa_post_update(trace.uuid_identification)

    return f"Import : {trace.flow_name}\n"
