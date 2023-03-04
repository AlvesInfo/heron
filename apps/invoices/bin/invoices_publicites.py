# pylint: disable=E0401
"""
Génération des factures de redevance de Pubilicité, vers le module edi_import
FR : Module de génération des factures de redevance de Pubilicité
EN : Module for generating Advertising fee invoices

Commentaire:

created at: 2023-03-03
created by: Paulo ALVES

modified at: 2023-03-03
modified by: Paulo ALVES
"""
from typing import AnyStr

from django.utils import timezone

from apps.data_flux.trace import get_trace


def publicity(dte_d: AnyStr, dte_f: AnyStr):
    """Génération de factures de redevance de Pubilicité
    :param dte_d: Date de début de période au format texte isoformat
    :param dte_f: Date de fin de période au format texte isoformat
    :return:
    """
    file_name = "redevance_publicite"
    trace_name = "Génération des redevances de publicité"
    application_name = "redevance_publicite"
    flow_name = "PUBLICITE"
    comment = ""
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)

    to_print = "Génération des redevances de publicité"

    trace.time_to_process = (timezone.now() - trace.created_at).total_seconds()
    trace.final_at = timezone.now()
    trace.save()

    return trace, to_print
