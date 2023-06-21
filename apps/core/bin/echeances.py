# pylint: disable=E0401,E1101,C0303,R0913,W0613,R0914
"""
FR : Module de calcul des échéances et fonction des modes de règlements
EN : Module for calculating deadlines and function of payment methods
Commentaire:

created at: 2023-06-21
created by: Paulo ALVES

modified at: 2023-06-21
modified by: Paulo ALVES
"""
import os
import platform
import sys
from typing import AnyStr, Tuple
from functools import lru_cache

import pendulum
import django

BASE_DIR = r"C:\SitesWeb\heron"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")

django.setup()

from apps.accountancy.models import ModeReglement


@lru_cache(maxsize=256)
def get_payment_method_elements(payment_method: AnyStr) -> Tuple:
    """
    Fonction qui renvoie les éléments de calculs des échéances en fonction du mode de règlement
    :param payment_method: Mode de règlement
    :return:
    """
    try:
        mode = ModeReglement.objects.get(a=payment_method)
    except ModeReglement.DoesNotExist:
        pass
