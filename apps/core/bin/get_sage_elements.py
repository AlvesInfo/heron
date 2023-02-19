# pylint: disable=E0401
"""
FR : Module pour retourner les UUID des axes par leur noms
EN : Module to return UUIDs of axes by their names

Commentaire:

created at: 2023-02-19
created by: Paulo ALVES

modified at: 2023-02-19
modified by: Paulo ALVES
"""
from uuid import UUID
from typing import Union
from functools import lru_cache

from apps.accountancy.models import SectionSage, AccountSage


@lru_cache(maxsize=256)
def get_uuid_pys(pys: str) -> Union[None, UUID]:
    """Retourne l'UUID de l'axe pys passé en paramètre"""

    pys_dict = dict(SectionSage.objects.pys_section().values_list("section", "uuid_identification"))

    return pys_dict.get(pys)


@lru_cache(maxsize=256)
def get_uuid_pro(pro: str) -> Union[None, UUID]:
    """Retourne l'UUID de l'axe pro passé en paramètre"""

    pro_dict = dict(SectionSage.objects.pro_section().values_list("section", "uuid_identification"))

    return pro_dict.get(pro)


@lru_cache(maxsize=256)
def get_uuid_cct(cct: str) -> Union[None, UUID]:
    """Retourne l'UUID de l'axe cct passé en paramètre"""

    cct_dict = dict(SectionSage.objects.cct_section().values_list("section", "uuid_identification"))

    return cct_dict.get(cct)


@lru_cache(maxsize=256)
def get_uuid_prj(prj: str) -> Union[None, UUID]:
    """Retourne l'UUID de l'axe prj passé en paramètre"""

    prj_dict = dict(SectionSage.objects.prj_section().values_list("section", "uuid_identification"))

    return prj_dict.get(prj)


@lru_cache(maxsize=256)
def get_uuid_bu(bu: str) -> Union[None, UUID]:
    """Retourne l'UUID de l'axe bu passé en paramètre"""

    bu_dict = dict(SectionSage.objects.bu_section().values_list("section", "uuid_identification"))

    return bu_dict.get(bu)


@lru_cache(maxsize=256)
def get_uuid_account(account: str, code_plan_sage: str = "FRA") -> Union[None, UUID]:
    """Retourne l'UUID du compte comptable passé en paramètre"""

    account_dict = dict(
        AccountSage.objects.filter(code_plan_sage=code_plan_sage, account=account).values_list(
            "account", "uuid_identification"
        )
    )

    return account_dict.get(account)
