# pylint: disable=E0401
"""
FR : Module de gestion des traces
EN : Log management module

Commentaire:

created at: 2022-04-08
created by: Paulo ALVES

modified at: 2022-04-08
modified by: Paulo ALVES
"""
from uuid import uuid4

from django.utils import timezone

from apps.data_flux.models import Trace


def get_trace(trace_name, file_name, application_name, flow_name, comment):
    """
    Créé la base de la trace
    :param trace_name: trace_name
    :param file_name: file_name
    :param application_name: application_name
    :param flow_name: flow_name
    :param comment: comment
    :return: Trace Object
    """
    trace = Trace.objects.create(
        created_at=timezone.now(),
        uuid_identification=uuid4(),
        trace_name=trace_name,
        file_name=file_name,
        application_name=application_name,
        flow_name=flow_name,
        comment=comment,
        created_numbers_records=0,
        updated_numbers_records=0,
        errors_numbers_records=0,
        unknown_numbers_records=0,
    )
    return trace
