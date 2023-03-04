# pylint: disable=E0401
"""
Numérotation interne, pour l'import dans l'EDI des founisseurs internes pour les ventes
FR : Module de récupération de la numérotation de factureinterne
EN : Internal invoices dialing recovery module

Commentaire:

created at: 2023-03-04
created by: Paulo ALVES

modified at: 2023-03-04
modified by: Paulo ALVES
"""
from typing import AnyStr


def internal_nums(dte_d: AnyStr, dte_f: AnyStr):
    """Génération d'un numéro de facture interne
    :param dte_d: Date de début de période au format texte isoformat
    :param dte_f: Date de fin de période au format texte isoformat
    :return:
    """
    flow_name = "INVOICES_INTERNAL_NUMS"
