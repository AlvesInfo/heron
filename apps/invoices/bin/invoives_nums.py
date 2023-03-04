# pylint: disable=E0401
"""
Numérotation Externe. N° de facture Enseigne pour les ventes
FR : Module de récupération de la numérotation de facture des Ventes Enseignes
EN : Module for retrieving the invoice numbering of Retail Sales

Commentaire:

created at: 2023-03-04
created by: Paulo ALVES

modified at: 2023-03-04
modified by: Paulo ALVES
"""
from typing import AnyStr


def external_nums(dte_d: AnyStr, dte_f: AnyStr):
    """Génération d'un numéro de facture de Vente Enseigne
    :param dte_d: Date de début de période au format texte isoformat
    :param dte_f: Date de fin de période au format texte isoformat
    :return:
    """
    flow_name = "INVOICES_NUMS"
