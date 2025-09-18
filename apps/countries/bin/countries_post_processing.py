# pylint: disable=E0401,C0303
"""
FR : Module de post-traitement avant import des fichiers sage pour l'application Countries
EN : Post-processing module before importing sage files for the Countries application

Commentaire:

created at: 2022-05-10
created by: Paulo ALVES

modified at: 2022-05-10
modified by: Paulo ALVES
"""
from django.db import connection


def pays_post_insert():
    """
    Mise à jour des champs dates vides à l'import des Pays Sage X3
    """
    sql_date = """
    update "countries_country"
    set 
        "cee_date" = case 
                        when "cee_date" = '1900-01-01' 
                        then null
                        else "cee_date"
                     end,
        "cee_date_quit" = case 
                        when "cee_date_quit" = '1900-01-01' 
                        then null
                        else "cee_date_quit"
                     end
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_date)
