# pylint: disable=E0401
"""
Numérotation générique
FR : Module de récupération de la numérotation générique
EN : Generic dialing recovery module

Commentaire:

created at: 2023-04-13
created by: Paulo ALVES

modified at: 2023-04-13
modified by: Paulo ALVES
"""
from typing import AnyStr

from apps.parameters.bin.core import get_counter_num
from apps.parameters.models import Counter


def get_generic_cct_num(cct: AnyStr) -> get_counter_num:
    """Génération d'un numéro générique unique
    :return:
    """
    counter = Counter.objects.get(name="generic")
    generic_cct_num = get_counter_num(
        counter_instance=counter,
        attr_instance_dict={"prefix": cct, "separateur": "_"},
    )

    return generic_cct_num


def get_folder_num() -> get_counter_num:
    """Génération d'un numéro générique unique
    :return:
    """
    counter = Counter.objects.get(name="folder_num")
    generic_folder_num = get_counter_num(
        counter_instance=counter,
        attr_instance_dict={},
    )

    return generic_folder_num
