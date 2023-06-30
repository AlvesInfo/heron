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

BASE_DIR = r"C:\SitesWeb\heron"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")

django.setup()

from django.db.models.fields import NOT_PROVIDED
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

    # Mise à jour des champs name (80 caract.), short_name (20 caract.), de book society
    with connection.cursor() as cursor:
        sql_update = """
        update "book_society" 
        set "name" = case 
                        when "name" isnull or "name" = '' 
                        then "third_party_num"
                        else "name"
                    end,
            "short_name" = case 
                                when "short_name" isnull or "short_name" = ''  
                                    then 
                                        case 
                                            when "name" isnull or "name" = '' 
                                            then "third_party_num"
                                            else LEFT("name", 20)
                                        end 
                                else "short_name"
                            end 
        """
        cursor.execute(sql_update)


def adress_sage_post_processing():
    """Mise à jour des champs pouvant avoir None dans les champs adresse...."""

    with connection.cursor() as cursor:

        # Mise à jour des valeurs 'None' dans book_address
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

        # Mise à jour avec l'adresse 1 de book society
        sql_adress_1 = """
        update "book_society" "bs" 
        set "address_code" = "ba"."address_code",
            "immeuble" = coalesce("ba"."immeuble", '') || ' - ' || coalesce("ba"."immeuble_02", ''),
            "adresse" =  coalesce("ba"."adresse", ''),
            "code_postal" = coalesce("ba"."code_postal", ''),
            "ville" = coalesce("ba"."ville", ''),
            "pays" = "ba"."pays",
            "email_01" = "ba"."email_01",
            "email_02" = "ba"."email_02",
            "email_03" = "ba"."email_03",
            "email_04" = "ba"."email_04",
            "email_05" = "ba"."email_05",
            "phone_number_01" = "ba"."phone_number_01",
            "mobile_number" = "ba"."mobile_number"
        from (
            select 
                "society" as "third_party_num",
                "address_code",
                "line_01" as "immeuble",
                "line_02" as "immeuble_02",
                "line_03" as "adresse",
                "postal_code" as "code_postal",
                "city" as "ville",
                "country" as "pays",
                "email_01",
                "email_02",
                "email_03",
                "email_04",
                "email_05",
                "phone_number_01",
                "mobile_number"
            from book_address ba 
            where address_code = '1'
        ) "ba"
        where "bs"."third_party_num" = "ba"."third_party_num"
        """
        cursor.execute(sql_adress_1)

        # Mise à jour des valeurs 'None' Dans book_society
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


if __name__ == "__main__":
    # bpr_book_post_processing()
    adress_sage_post_processing()
