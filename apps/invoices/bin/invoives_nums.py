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
import pendulum

from apps.parameters.bin.core import get_counter_num
from apps.parameters.models import Counter


def get_invoice_num(invoice_dte: pendulum.instance):
    """Génération d'un numéro de facture de Vente Enseigne
    :param invoice_dte: Date de la facture (instance de pendulumm
    :return:
    """
    counter = Counter.objects.get(name="invoices_num")
    fac_num = get_counter_num(
        counter_instance=counter,
        attr_instance_dict={"prefix": invoice_dte},
    )

    return fac_num
