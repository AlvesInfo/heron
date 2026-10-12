"""Numérotation générique.

FR : Module de récupération de la numérotation générique
EN : Generic dialing recovery module.

Commentaire:

created at: 2023-04-13
created by: Paulo ALVES

modified at: 2023-04-13
modified by: Paulo ALVES
"""

from apps.parameters.bin.core import get_counter_num
from apps.parameters.models import Counter


def get_generic_cct_num(cct: str) -> str:
    """Génération d'un numéro générique unique.

    :return:
    """
    counter = Counter.objects.get(name="generic")
    return get_counter_num(
        counter_instance=counter,
        attr_instance_dict={"prefix": cct, "separateur": "_"},
    )
