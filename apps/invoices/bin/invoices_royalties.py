# pylint: disable=E0401
"""
Génération des factures de Royalties, vers le module edi_import
FR : Module de génération des factures de Royalties
EN : Royalties invoice generation module

Commentaire:

created at: 2023-03-03
created by: Paulo ALVES

modified at: 2023-03-03
modified by: Paulo ALVES
"""
from typing import AnyStr

from django.utils import timezone

from apps.data_flux.trace import get_trace
from apps.users.models import User


def royalties(dte_d: AnyStr, dte_f: AnyStr, user: User):
    """Génération de factures de Royalties
    :param dte_d: Date de début de période au format texte isoformat
    :param dte_f: Date de fin de période au format texte isoformat
    :param user: Utilisateur lançant la génération
    :return:
    """
    file_name = "royalties"
    trace_name = "Génération des royalties"
    application_name = "royalties"
    flow_name = "ROYALTIES"
    comment = ""
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)

    to_print = "Génération des royalties"

    trace.time_to_process = (timezone.now() - trace.created_at).total_seconds()
    trace.final_at = timezone.now()
    trace.created_by = user
    trace.save()

    return trace, to_print
