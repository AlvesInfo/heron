# pylint: disable=
"""
FR : Module d'import des modèles de Sage X3
EN : Import module for Sage X3 models

Commentaire:

created at: 2022-04-08
created by: Paulo ALVES

modified at: 2022-04-08
modified by: Paulo ALVES
"""
from apps.accountancy.models import SectionSage, CctSage


def update_cct_sage():
    """Update de la table CctSage, pour le foreign key dans les clients des centrales"""
    cct_section = SectionSage.objects.filter(axe="CCT")

    for cct in cct_section:
        CctSage.objects.update_or_create(
            cct=cct.section,
            name=cct.name,
            short_name=cct.short_name,
            chargeable=cct.chargeable,
            regroup_01=cct.regroup_01,
            regroup_02=cct.regroup_02,
            uuid_identification=cct.uuid_identification,
        )


if __name__ == '__main__':
    update_cct_sage()
