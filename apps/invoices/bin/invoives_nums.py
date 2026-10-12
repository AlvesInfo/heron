"""Numérotation Externe. N° de facture Enseigne pour les ventes.

FR : Module de récupération de la numérotation de facture des Ventes Enseignes
EN : Module for retrieving the invoice numbering of Retail Sales.

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
    """Génération d'un numéro de facture de Vente Enseigne.

    :param invoice_dte: Date de la facture (instance de pendulumm
    :return:
    """
    counter = Counter.objects.get(name="invoices_num")
    return get_counter_num(
        counter_instance=counter,
        attr_instance_dict={"prefix": invoice_dte},
    )


def get_purchase_num():
    """Génération d'un numéro de facture de Vente Enseigne.

    :return:
    """
    counter = Counter.objects.get(name="purchase_num")
    return get_counter_num(
        counter_instance=counter,
    )


def get_bicpar_num():
    """Génération d'un numéro des fichiers d'export x3 des factures de vente.

    :return:
    """
    counter = Counter.objects.get(name="bicpar_num")
    return get_counter_num(
        counter_instance=counter,
    )


def get_bispar_num():
    """Génération d'un numéro de l'export x3 des factures d'achat.

    :return:
    """
    counter = Counter.objects.get(name="bispar_num")
    return get_counter_num(
        counter_instance=counter,
    )


def get_bispard_num():
    """Génération d'un numéro de l'export x3 des factures d'achat.

    :return:
    """
    counter = Counter.objects.get(name="bispard_num")
    return get_counter_num(
        counter_instance=counter,
    )


def get_gaspar_num():
    """Génération d'un numéro de l'export x3 des od.

    :return:
    """
    counter = Counter.objects.get(name="gaspar_num")
    return get_counter_num(
        counter_instance=counter,
    )


def get_bispa_num():
    """Génération d'un numéro de l'export x3 des factures d'achat.

    :return:
    """
    counter = Counter.objects.get(name="bispa_num")
    return get_counter_num(
        counter_instance=counter,
    )


def get_zip_num():
    """Génération d'un numéro du fichier zip de l'export total.

    :return:
    """
    counter = Counter.objects.get(name="generic")
    return get_counter_num(
        counter_instance=counter,
        attr_instance_dict={
            "prefix": "ZIP",
            "suffix": str(pendulum.now().date().isoformat()).replace("-", "_"),
            "separateur": "_",
        },
    )
