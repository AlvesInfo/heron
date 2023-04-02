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

from django.db import connection

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


def adress_sage_post_processing():
    """Mise à jour des champs pouvant avoir non dans les champs adresse...."""

    # mise à jour des valeurs 'None'
    with connection.cursor() as cursor:
        # Dans book_society
        sql_book_society = """
        update "book_society" 
        set "adresse" = case when upper("adresse") = 'NONE' then null else "adresse" end,
            "code_postal" = case 
                                when upper("code_postal") = 'NONE' 
                                then null 
                                else "code_postal" 
                            end,
            "email" = case when upper("email") = 'NONE' then null else "email" end,
            "immeuble" = case when upper("immeuble") = 'NONE' then null else "immeuble" end,
            "mobile" = case when upper("mobile") = 'NONE' then null else "mobile" end,
            "pays" = case when upper("pays") = 'NONE' then null else "pays" end,
            "telephone" = case when upper("telephone") = 'NONE' then null else "telephone" end,
            "ville" = case when upper("ville") = 'NONE' then null else "ville" end
        where
            upper("adresse")= 'NONE'
            or
            upper("code_postal")= 'NONE'
            or
            upper("email")= 'NONE'
            or
            upper("immeuble")= 'NONE'
            or
            upper("mobile")= 'NONE'
            or
            upper("pays")= 'NONE'
            or
            upper("telephone")= 'NONE'
            or
            upper("ville")= 'NONE'
        """
        cursor.execute(sql_book_society)

        # Dans book_address
        sql_book_adress = """
        update "book_address"
        set "line_01" = case when upper("line_01") = 'NONE' then null else "line_01" end,
            "line_02" = case when upper("line_02") = 'NONE' then null else "line_02" end,
            "line_03" = case when upper("line_03") = 'NONE' then null else "line_03" end,
            "phone_number_01" = case 
                                    when upper("phone_number_01") = 'NONE' 
                                    then null 
                                    else "phone_number_01" 
                                end,
                                    "phone_number_02" = case 
                                    when upper("phone_number_02") = 'NONE' 
                                    then null 
                                    else "phone_number_02" 
                                end,
                                    "phone_number_03" = case 
                                    when upper("phone_number_03") = 'NONE' 
                                    then null 
                                    else "phone_number_03" 
                                end,
                                    "phone_number_04" = case 
                                    when upper("phone_number_04") = 'NONE' 
                                    then null 
                                    else "phone_number_04" 
                                end,
                                    "phone_number_05" = case 
                                    when upper("phone_number_05") = 'NONE' 
                                    then null 
                                    else "phone_number_05" 
                                end
        where
            upper("line_01")= 'NONE'
            or
            upper("line_02")= 'NONE'
            or
            upper("line_03")= 'NONE'
            or
            upper("phone_number_01")= 'NONE'
            or
            upper("phone_number_02")= 'NONE'
            or
            upper("phone_number_03")= 'NONE'
            or
            upper("phone_number_04")= 'NONE'
            or
            upper("phone_number_05")= 'NONE';        
        """
        cursor.execute(sql_book_adress)


if __name__ == "__main__":
    # bpr_book_post_processing()
    adress_sage_post_processing()
