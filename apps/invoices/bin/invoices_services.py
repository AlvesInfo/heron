# pylint: disable=E0401
"""
Génération des factures de Prestations, vers le module edi_import
FR : Module de génération des factures de Prestations
EN : Service invoice generation module

Commentaire:

created at: 2023-03-03
created by: Paulo ALVES

modified at: 2023-03-03
modified by: Paulo ALVES
"""
from typing import AnyStr

from django.utils import timezone

from apps.data_flux.trace import get_trace


def services(dte_d: AnyStr, dte_f: AnyStr):
    """Génération de factures de Prestations
    :param dte_d: Date de début de période au format texte isoformat
    :param dte_f: Date de fin de période au format texte isoformat
    :return:
    """
    file_name = "prestations"
    trace_name = "Génération des prestations"
    application_name = "prestations"
    flow_name = "PRESTATIONS"
    comment = ""
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)

    to_print = "Génération des prestations"

    trace.time_to_process = (timezone.now() - trace.created_at).total_seconds()
    trace.final_at = timezone.now()
    trace.save()

    return trace, to_print
