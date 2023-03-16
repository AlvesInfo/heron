# pylint: disable=E0401
"""
FR : Module de récupération de la numérotation de facture des saisies manuelles
EN : Module for recovering invoice numbering from manual entries

Commentaire:

created at: 2023-03-04
created by: Paulo ALVES

modified at: 2023-03-04
modified by: Paulo ALVES
"""
from typing import AnyStr


def invoices_manual_entries_nums(third_party_num: AnyStr):
    """Génération d'un numéro de facture, pour celles saisies manuellement
    :param third_party_num: N° Tiers
    :return: invoice_num
    """
