# pylint: disable=E0401,C0413,W0718
"""
FR : Module de mise à jour des éléments nécessaires à la facturation
EN : Module for updating the elements necessary for invoicing

Commentaire:

created at: 2023-03-27
created by: Paulo ALVES

modified at: 2023-03-27
modified by: Paulo ALVES
"""
import os
import platform
import sys
from datetime import datetime
import time

import django
from django.db import connection, transaction

BASE_DIR = r"/"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")
django.setup()

from heron.loggers import LOGGER_IMPORT
from apps.data_flux.trace import get_trace


@transaction.atomic
def centers_invoices_update():
    """Mise à jour des Centrales / Enseignes pour la facturation"""
    trace_name = "Mise à jour des Centrales / Enseignes pour la facturation"
    file_name = "insert into ..."
    application_name = "centers_invoices_update"
    flow_name = "centers_invoices_update"
    comment = "Mise à jour historique Centrales pour la facturation"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)

    with connection.cursor() as cursor:
        sql_create = """
        insert into invoices_centersinvoices
        (
            created_at,
            "uuid_identification",
            -- Centrale fille
            "code_center",
            "comment_center",
            "legal_notice_center",
            "bank_center",
            "iban_center",
            "code_swift_center"
        )
        select
            now() as created_at,
            gen_random_uuid() as "uuid_identification",
            -- Centrale fille
            "cpc"."code" as "code_center",
            case when "cpc"."comment" isnull then '' else "cpc"."comment" end as "comment_center",
            case 
                when "cpc"."legal_notice" isnull then '' else "cpc"."legal_notice" 
            end as "legal_notice_center",
            case when "cpc"."bank" isnull then '' else "cpc"."bank" end as "bank_center",
            case when "cpc"."iban" isnull then '' else "cpc"."iban" end as "iban_center",
            case 
                when "cpc"."code_swift" isnull then '' else "cpc"."code_swift" 
            end as "code_swift_center"
        from "centers_purchasing_childcenterpurchase" "cpc"  
        on conflict do nothing
        """
        cursor.execute(sql_create)
        trace.created_numbers_records = cursor.rowcount
        trace.save()

    return trace


@transaction.atomic
def signboards_invoices_update():
    """Mise à jour des Centrales / Enseignes pour la facturation"""
    trace_name = "Mise à jour des Centrales / Enseignes pour la facturation"
    file_name = "insert into ..."
    application_name = "centers_invoices_update"
    flow_name = "centers_invoices_update"
    comment = "Mise à jour historique Enseignes pour la facturation"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)

    with connection.cursor() as cursor:
        sql_create = """
        insert into invoices_signboardsinvoices
        (
            created_at,
            "uuid_identification",
            -- Enseigne
            "code_signboard",
            "logo_signboard",
            "message"
        )
        select
            now() as created_at,
            gen_random_uuid() as "uuid_identification",
            -- Enseigne
            "cps"."code" as "code_signboard",
            case when "cps"."logo" isnull then '' else "cps"."logo" end as "logo_signboard",
            case when "cps"."message" isnull then '' else "cps"."message" end as "message"
        from "centers_purchasing_signboard" "cps"
        on conflict do nothing
        """
        cursor.execute(sql_create)
        trace.created_numbers_records = cursor.rowcount
        trace.save()

    return trace


@transaction.atomic
def parties_invoices_update():
    """Mise à des parties prenante dans la facturation"""
    trace_name = "Mise à des parties prenante dans la facturation"
    file_name = "insert into ..."
    application_name = "parties_invoices_update"
    flow_name = "parties_invoices_update"
    comment = "Mise à jour historique des parties prenantes dans la facturation"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)

    with connection.cursor() as cursor:
        sql_create = """
        insert into invoices_partiesinvoices
        (
            created_at,
            "uuid_identification",
            -- CCT
            "cct",
            "name_cct",
            "immeuble_cct",
            "adresse_cct",
            "code_postal_cct",
            "ville_cct",
            "pays_cct",
            -- Tiers facturé à qui appartient le CCT
            "third_party_num",
            "name_third_party",
            "immeuble_third_party",
            "adresse_third_party",
            "code_postal_third_party",
            "ville_third_party",
            "pays_third_party"
        )
        select
            now() as created_at,
            gen_random_uuid() as "uuid_identification",
            -- CCT
            "ccm"."cct",
            case 
                when "ccm"."invoice_entete" isnull or "ccm"."invoice_entete" = '' 
                then  case when "ccm"."intitule" isnull then '' else "ccm"."intitule" end 
                else "ccm"."invoice_entete"
            end as "name_cct", 
            case 
                when "ccm"."immeuble" isnull or UPPER("ccm"."immeuble") = 'NONE' 
                then '' 
                else "ccm"."immeuble" 
            end as "immeuble_cct",
            case 
                when "ccm"."adresse" isnull or UPPER("ccm"."adresse") = 'NONE' 
                then '' 
                else "ccm"."adresse" 
            end as "adresse_cct",
            case 
                when "ccm"."code_postal" isnull or UPPER("ccm"."code_postal") = 'NONE'
                then '' 
                else "ccm"."code_postal" 
            end as "code_postal_cct",
            case 
                when "ccm"."ville" isnull or UPPER("ccm"."ville") = 'NONE'
                then '' 
                else "ccm"."ville" 
            end as "ville_cct",
            case 
                when "com"."country_name" isnull or UPPER("com"."country_name") = 'NONE'
                then '' 
                else "com"."country_name" 
            end as "pays_cct",
            -- Tiers facturé à qui appartient le CCT
            "bs"."third_party_num",
            case 
                 when "bs"."invoice_entete" isnull or "bs"."invoice_entete" = '' 
                then  case when "bs"."name" isnull then '' else "bs"."name" end 
                else "bs"."invoice_entete"
            end as "name_third_party",
            case 
                when "bs"."immeuble" isnull or UPPER("bs"."immeuble") = 'NONE'
                then '' 
                else "bs"."immeuble" 
            end as "immeuble_third_party",
            case 
                when "bs"."adresse" isnull or UPPER("bs"."adresse") = 'NONE'
                then '' 
                else "bs"."adresse" 
            end as "adresse_third_party",
            case 
                when "bs"."code_postal" isnull or UPPER("bs"."code_postal") = 'NONE'
                then '' 
                else "bs"."code_postal" 
            end as "code_postal_third_party",
            case 
                when "bs"."ville" isnull or UPPER("bs"."ville") = 'NONE'
                then '' 
                else "bs"."ville" 
            end as "ville_third_party",
            case 
                when "bsm"."country_name" isnull or UPPER("bsm"."country_name") = 'NONE'
                then '' 
                else "bsm"."country_name"  
            end as "pays_third_party"
        from "centers_clients_maison" "ccm"
        left join "book_society" "bs"  
        on "ccm"."third_party_num" = "bs"."third_party_num" 
        left join "countries_country" "com"
        on "com"."country" = "ccm"."pays"
        left join "countries_country" "bsm"
        on "bsm"."country" = "bs"."pays"
        on conflict do nothing
        """
        cursor.execute(sql_create)
        trace.created_numbers_records = cursor.rowcount
        trace.save()

    return trace


def process():
    """
    Mise à jour des CentersInvoices, SignboardsInvoices et PartiesInvoices
    pour figer l'historique des parties prenantes dans la facturation
    """
    processings_list = [
        centers_invoices_update,
        signboards_invoices_update,
        parties_invoices_update,
    ]

    for processing in processings_list:
        error = False
        trace = None
        traceback = ""

        try:
            trace = processing()

        except Exception as except_error:
            error = True
            traceback = f"Exception Générale: {processing.__name__}\n{except_error!r}"
            LOGGER_IMPORT.exception(traceback)

        finally:
            if error and trace:
                trace.errors = True
                trace.comment = (
                    trace.comment
                    + "\n. Une erreur c'est produite veuillez consulter les logs :\n"
                    + traceback
                )
            if trace is not None:
                trace.save()


if __name__ == "__main__":
    while True:
        maintenant = datetime.now()
        heure = maintenant.hour
        minute = maintenant.minute

        if heure == 6 and minute == 30:
            print(
                "Mise à jour des CentersInvoices, SignboardsInvoices et PartiesInvoices : ",
                maintenant,
            )
            process()

        time.sleep(60)
