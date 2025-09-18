# pylint: disable=
"""
FR : Mise à jour des cct sage par extraction depuis la table CctSage et après sa mise à jour depuis
     fichier ZBI exporter depuis Sage X3
EN : Update of sage ccts by extraction from the CctSage table and after its update from ZBI file
     export from Sage X3

Commentaire:

created at: 2022-04-08
created by: Paulo ALVES

modified at: 2022-04-08
modified by: Paulo ALVES
"""
import os
import sys
import platform

import django

BASE_DIR = r"/"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")

django.setup()

from apps.accountancy.models import SectionSage, CctSage


def update_cct_sage():
    """Update de la table CctSage, pour le foreign key dans les clients des centrales"""
    section = SectionSage.objects.filter(axe="CCT")

    for cct_section in section:
        try:
            cct = CctSage.objects.get(cct=cct_section.section)
            cct.name = cct_section.name
            cct.short_name = cct_section.short_name
            cct.chargeable = cct_section.chargeable
            cct.regroup_01 = cct_section.regroup_01
            cct.regroup_02 = cct_section.regroup_02
            cct.active = cct_section.active
            cct.save()

        except CctSage.DoesNotExist:
            cct = CctSage(
                cct=cct_section.section,
                name=cct_section.name,
                short_name=cct_section.short_name,
                chargeable=cct_section.chargeable,
                regroup_01=cct_section.regroup_01,
                regroup_02=cct_section.regroup_02,
                uuid_identification=cct_section.uuid_identification,
                active=cct_section.active
            )
            cct.save()


if __name__ == '__main__':
    update_cct_sage()
