# pylint: disable=E0401,C0303
"""
FR : Reset des imports
EN : Reset imports

Commentaire:

created at: 2022-08-17
created by: Paulo ALVES

modified at: 2022-08-17
modified by: Paulo ALVES
"""
from apps.edi.models import EdiImport


def reset_all_imports():
    """
    Reset de tous les edi imports, saisie, etc., pour une nouvelle période de programmation
    :return: None
    """
    EdiImport.objects.all().delete()
