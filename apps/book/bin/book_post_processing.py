# pylint: disable=E0401,C0413,W0212
"""
FR : Module de post-traitement après import des fichiers Sage X3
EN : Post-processing module before importing Sage X3 files

Commentaire:

created at: 2022-05-10
created by: Paulo ALVES

modified at: 2022-05-10
modified by: Paulo ALVES
"""
import os
import platform
import sys
import django
from django.db.models.fields import NOT_PROVIDED

BASE_DIR = r"C:\SitesWeb\heron"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")
django.setup()

from apps.book.models import Society


def bpr_book_post_processing():
    """
    Suppression des valeurs null dans la table Society,
    pour les champs integrable, chargeable, od_ana
    """
    integrable = Society._meta.get_field("integrable").default
    integrable = False if integrable == NOT_PROVIDED else integrable
    Society.objects.filter(integrable__isnull=True).update(integrable=integrable)

    chargeable = Society._meta.get_field("chargeable").default
    chargeable = False if chargeable == NOT_PROVIDED else chargeable
    Society.objects.filter(chargeable__isnull=True).update(chargeable=chargeable)

    od_ana = Society._meta.get_field("od_ana").default
    od_ana = False if od_ana == NOT_PROVIDED else od_ana
    Society.objects.filter(od_ana__isnull=True).update(od_ana=od_ana)


if __name__ == "__main__":
    bpr_book_post_processing()
