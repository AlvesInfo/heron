# pylint: disable=E0401,R0903,C0413,E1101
"""
FR : Module du modèle des maisons
EN : Houses model module

Commentaire:

created at: 2022-04-07
created by: Paulo ALVES

modified at: 2022-04-07
modified by: Paulo ALVES
"""
from copy import deepcopy
import os
import platform
import sys
from datetime import datetime
import time

import django

BASE_DIR = r"C:\SitesWeb\heron"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")
django.setup()

from django.db import connection

from apps.countries.models import Country
from apps.centers_clients.models import MaisonBi


def import_maisons_bi():
    """Import des maisons depuis la B.I"""
    with connection.cursor() as cursor:
        sql_maisons = """
        select
            left("code_maison", 15) as "code_maison",
            left("intitule", 50) as "intitule",
            case 
                when "affaire"='' or "affaire" isnull 
                then left("intitule_court", 12)
                else left("affaire", 12) 
            end as "intitule_court",
            left("code_cosium", 15) as "code_cosium",
            left("compte_bbgr", 15) as "compte_bbgr",
            "date_ouverture",
            "date_fermeture",
            left("immeuble", 200) as "immeuble",
            left("adresse", 200) as "adresse",
            left("code_postal", 15) as "code_postal",
            left("ville", 50) as "ville",
            left("pays_x3", 2) as "pays_x3",
            left("telephone", 25) as "telephone",
            left("email", 85) as "email"
        from heron_bi_maisons
        """
        cursor.execute(sql_maisons)

        list_fields = [
            "code_maison",
            "intitule",
            "intitule_court",
            "code_cosium",
            "code_bbgr",
            "opening_date",
            "closing_date",
            "immeuble",
            "adresse",
            "code_postal",
            "ville",
            "pays",
            "telephone",
            "email",
        ]
        i = 0

        for i, maison in enumerate(cursor.fetchall(), 1):
            maison_dict = dict(zip(list_fields, maison))

            try:
                maison_dict["pays"] = Country.objects.get(country=maison_dict.get("pays"))
            except Country.DoesNotExist:
                maison_dict["pays"] = None

            maison = MaisonBi.objects.filter(code_maison=maison_dict.get("code_maison"))

            if not maison.exists():
                MaisonBi.objects.create(**maison_dict)
            else:
                maison = (
                    MaisonBi.objects.filter(code_maison=maison_dict.get("code_maison"))
                    .values(
                        "code_maison",
                        "intitule",
                        "intitule_court",
                        "code_cosium",
                        "code_bbgr",
                        "opening_date",
                        "closing_date",
                        "immeuble",
                        "adresse",
                        "code_postal",
                        "ville",
                        "pays",
                        "telephone",
                        "email",
                    )
                    .first()
                )
                maison_test = deepcopy(maison_dict)
                maison_test["pays"] = maison_test.get("pays").country

                if maison != maison_test:
                    MaisonBi.objects.filter(code_maison=maison_dict.get("code_maison")).update(
                        **{
                            **{"is_modify": True},
                            **{
                                key: value
                                for key, value in maison_dict.items()
                                if key != "code_maison"
                            },
                        }
                    )

        print(i, "maisons importées ou mises à jour")


if __name__ == "__main__":

    while True:
        maintenant = datetime.now()
        heure = maintenant.hour
        minute = maintenant.minute

        if heure == 7 and minute == 00:
            print("lancement import maisons_bi : ", maintenant)
            import_maisons_bi()

        time.sleep(60)
