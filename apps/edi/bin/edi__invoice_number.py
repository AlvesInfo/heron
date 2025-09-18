# pylint: disable=E0401
"""
Numérotation interne, pour l'import dans l'EDI des founisseurs internes,
pour les ventes ou les saisies manuelles
FR : Module de récupération de la numérotation de facture interne ou saisies
EN : Module for retrieving internal invoice numbering or entries

Commentaire:

created at: 2023-03-11
created by: Paulo ALVES

modified at: 2023-03-11
modified by: Paulo ALVES
"""
from typing import AnyStr

import pendulum

from apps.parameters.models import Counter


def get_invoice_number(dte_d: pendulum):
    """Génération d'un numéro de facture interne
    :param dte_d: Date facture
    :return:
    """
    try:
        num_model = Counter.objects.get(function="INVOICES_NUMS")
    except:
        ...
