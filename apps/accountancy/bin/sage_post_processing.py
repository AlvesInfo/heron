# pylint: disable=E0401
"""
FR : Module de post-traitement après import des fichiers sage
EN : Pre-processing module before importing sage files

Commentaire:

created at: 2025-03-14
created by: Paulo ALVES

modified at: 2025-03-14
modified by: Paulo ALVES
"""

from apps.accountancy.models import VatRatSage


def rat_vat_correction():
    """
    Mise à 0 des taux de TVA pour le taux 011. Dans sage ce taux s'intègre à 0 car il n'existe que
    pour le calcul de la tva intrécommunautaire à 20%. Enrevanche, si on garde le taux de 20% dans H
    éron alors la facture sera à 20% alors que ce n'est pas le cas en réalité.
    On doit donc mettre ce taux à Zéro après l'import du matin.
    :return: None
    """

    VatRatSage.objects.filter(vat="011").update(rate=0)
