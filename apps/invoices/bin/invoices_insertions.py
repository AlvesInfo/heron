# pylint: disable=E0401
"""
FR : Module d'insertion provisoire
EN : Provisional insert module

Commentaire:

created at: 2023-03-11
created by: Paulo ALVES

modified at: 2023-03-11
modified by: Paulo ALVES
"""

from apps.edi.bin.cct_update import update_cct_edi_import
from apps.invoices.bin.pre_controls import control_alls_missings


def insertion_invoices():
    """Inserion des factures en mode provisoire avant la validation définitive"""

    # On update dabord les cct puis les centre et enseignes
    update_cct_edi_import()

    # Pré-contrôle des données avant insertion
    controls = control_alls_missings()

    if controls:
        # TODO : FAIRE LE PRE CONTROLE QUAND TOUS LE PROCESS EST TERMINE
        # Renvoyer une erreur si le pré-cotrôle n'est pas vide
        ...

