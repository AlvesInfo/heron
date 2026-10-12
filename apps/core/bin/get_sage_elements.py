"""FR : Module pour retourner les UUID des axes par leur noms.

EN : Module to return UUIDs of axes by their names.

Commentaire:

created at: 2023-02-19
created by: Paulo ALVES

modified at: 2023-02-19
modified by: Paulo ALVES
"""

from functools import lru_cache
from uuid import UUID

from apps.accountancy.models import SectionSage, VatSage


@lru_cache(maxsize=256)
def get_uuid_pys(pys: str) -> UUID | None:
    """Retourne l'UUID de l'axe pys passé en paramètre."""
    pys_dict = dict(SectionSage.objects.pys_section().values_list("section", "uuid_identification"))

    return pys_dict.get(pys)


@lru_cache(maxsize=256)
def get_uuid_pro(pro: str) -> UUID | None:
    """Retourne l'UUID de l'axe pro passé en paramètre."""
    pro_dict = dict(SectionSage.objects.pro_section().values_list("section", "uuid_identification"))

    return pro_dict.get(pro)


@lru_cache(maxsize=256)
def get_uuid_prj(prj: str) -> UUID | None:
    """Retourne l'UUID de l'axe prj passé en paramètre."""
    prj_dict = dict(SectionSage.objects.prj_section().values_list("section", "uuid_identification"))

    return prj_dict.get(prj)


@lru_cache(maxsize=256)
def get_uuid_bu(bu: str) -> UUID | None:
    """Retourne l'UUID de l'axe bu passé en paramètre."""
    bu_dict = dict(SectionSage.objects.bu_section().values_list("section", "uuid_identification"))

    return bu_dict.get(bu)


@lru_cache(maxsize=256)
def get_uuid_rfa(rfa: str) -> UUID | None:
    """Retourne l'UUID de l'axe rfa passé en paramètre."""
    rfa_dict = dict(SectionSage.objects.rfa_section().values_list("section", "uuid_identification"))

    return rfa_dict.get(rfa) or rfa_dict.get("NAF")


@lru_cache(maxsize=256)
def get_vat_regime(vat: str) -> str | None:
    """Retourne le vat regime en fonction de la tva."""
    try:
        vat_regime = VatSage.objects.get(vat=vat).vat_regime
    except VatSage.DoesNotExist:
        vat_regime = "FRA"

    return vat_regime
