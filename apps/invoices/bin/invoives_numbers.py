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

import pendulum

from apps.parameters.models import Counter


def get_counter(counter_name: AnyStr) -> Counter:
    """Renvoie le compteur de numérotation demandé,
    si il ne le trouve pas alors il crée et renvoie un générique
    :param counter_name: "nom du compteur"
    :return:
    """


def get_sales_invoice_number(dte_d: AnyStr):
    """Génération d'un numéro de facture de vente
    :param dte_d: Date facture
    :return:
    """
    counter_name = ""
    num_model = Counter.objects.filter

