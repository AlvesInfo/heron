# pylint: disable=
# E0401,E1101,W0703,W1203
"""
FR : Module de gestion des exclusions pour la facturation des Clients
EN : Exclusion management module for Customer billing

Commentaire:

created at: 2023-03-12
created by: Paulo ALVES

modified at: 2023-03-12
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

from django.db import connection

SQL_DELETE_MAISON_SUPPLIER = """
delete from "edi_ediimport" "ee"
where exists (
    select 1 
    from "centers_clients_maisonsupllierexclusion" "ccm"
    where "ee"."third_party_num" = "ccm"."third_party_num" 
    and "ee"."cct_uuid_identification" = "ccm"."cct_uuid_identification"
)
"""

SQL_DELETE_COUNTRY_SUPPLIER = """
delete from "edi_ediimport" "ee"
where exists (
    select 1 
    from ( 
        select 
            "cm"."uuid_identification" as "cct_uuid_identification", 
            "ce"."third_party_num" 
        from "centers_clients_suplliercountryexclusion" "ce"
        join "centers_clients_maison" "cm" 
        on "ce"."pays" = "cm"."pays" 
    ) "ccm" 
    where "ee"."third_party_num" = "ccm"."third_party_num" 
    and "ee"."cct_uuid_identification" = "ccm"."cct_uuid_identification"
)
"""

SQL_UPDATE_INCOICE_MONT = """
update "edi_ediimport" "edi"
set 
    "invoice_amount_without_tax" = "rex"."invoice_amount_without_tax",
    "invoice_amount_tax" = "rex"."invoice_amount_tax",
    "invoice_amount_with_tax" = "rex"."invoice_amount_with_tax"
from (
    select 
        "uuid_identification",
        "invoice_number",
        "third_party_num",
        sum("net_amount") as "invoice_amount_without_tax",
        sum("vat_amount") as "invoice_amount_tax",
        sum("amount_with_vat") as "invoice_amount_with_tax"
    from "edi_ediimport" "ee" 
    where exists (
        select 1 
            from (
            select 
                "third_party_num"
            from (
                select 
                    "third_party_num"
                from "centers_clients_maisonsupllierexclusion" "ccm" 
                union all
                select 
                    "third_party_num"
                from "centers_clients_suplliercountryexclusion" "ccs" 
            ) ex 
            group by "third_party_num" 
        ) "thirds" 
        where "thirds"."third_party_num" = "ee"."third_party_num"
    )
    group by     
        "uuid_identification",
        "invoice_number",
        "third_party_num"
) "rex" 
where "edi"."uuid_identification" = "rex"."uuid_identification"
and "edi"."invoice_number" = "rex"."invoice_number"
and "edi"."third_party_num" = "rex"."third_party_num"
"""


def set_exclusions():
    """Supprimer toutes les lignes d'écritures d'edi_ediimport qui font parties des exclusions"""

    with connection.cursor() as cursor:
        # Exclusions MaisonSupllierExclusion
        cursor.execute(SQL_DELETE_MAISON_SUPPLIER)

        # Exclusions SupllierCountryExclusion
        cursor.execute(SQL_DELETE_COUNTRY_SUPPLIER)

        # Mise à jour des totaux par factures
        cursor.execute(SQL_UPDATE_INCOICE_MONT)


if __name__ == "__main__":
    set_exclusions()
