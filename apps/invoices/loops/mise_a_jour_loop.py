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

BASE_DIR = r"/"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")

django.setup()

from django.db import connection, transaction
from django.utils import timezone

from heron.loggers import LOGGER_IMPORT
from apps.data_flux.trace import get_trace


@transaction.atomic
def centers_invoices_update():
    """Mise à jour des Centrales pour la facturation"""
    trace_name = "Mise à jour des Centrales pour la facturation"
    file_name = "insert into ..."
    application_name = "centers_invoices_update"
    flow_name = "centers_invoices_update"
    comment = "Mise à jour historique Centrales pour la facturation"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)

    with connection.cursor() as cursor:
        # ON Supprime les codes non utilisés
        sql_create = """
        insert into invoices_centersinvoices
        (
            "created_at",
            "uuid_identification",
            -- Centrale fille
            "code_center",
            "comment_center",
            "legal_notice_center",
            "footer",
            "bank_center",
            "iban_center",
            "code_swift_center",
            "vat_regime_center",
            "member_num",
            "cpy",
            "fcy"
        )
        select
            now() as created_at,
            coalesce("ic"."uuid_identification", gen_random_uuid()) as "uuid_identification",
            -- Centrale fille
            "cpc"."code" as "code_center",
            coalesce("cpc"."comment", '') as "comment_center",
            coalesce("cpc"."legal_notice", '') as "legal_notice_center",
            coalesce("cpc"."footer", '') as "footer",
            coalesce("cpc"."bank", '') as "bank_center",
            coalesce("cpc"."iban", '') as "iban_center",
            coalesce("cpc"."code_swift", '') as "code_swift_center",
            coalesce("av"."vat_regime", 'FRA') as "vat_regime_center",
            coalesce("cpc"."member_num", '') as "member_num",
            coalesce("cpc"."societe_cpy_x3", '') as "cpy",
            coalesce("cpc"."site_fcy_x3", '') as "fcy"
        from "centers_purchasing_childcenterpurchase" "cpc"  
        left join "accountancy_vatregimesage" "av"
        on "cpc"."vat_regime_center" = "av"."uuid_identification"
        left join "invoices_centersinvoices" "ic" 
        on "ic"."code_center" = "cpc"."code"
        and coalesce("ic"."comment_center", '') = coalesce("cpc"."comment", '')
        and coalesce("ic"."legal_notice_center", '') = coalesce("cpc"."legal_notice", '')
        and coalesce("ic"."footer", '') = coalesce("cpc"."footer", '')
        and coalesce("ic"."bank_center", '') = coalesce("cpc"."bank", '')
        and coalesce("ic"."iban_center", '') = coalesce("cpc"."iban", '')
        and coalesce("ic"."code_swift_center", '') = coalesce("cpc"."code_swift", '')
        and coalesce("ic"."vat_regime_center", 'FRA') = coalesce("av"."vat_regime", 'FRA')
        and coalesce("ic"."member_num", '') = coalesce("cpc"."member_num", '')
        and coalesce("ic"."cpy", '') = coalesce("cpc"."societe_cpy_x3", '')
        and coalesce("ic"."fcy", '') = coalesce("cpc"."site_fcy_x3", '')
        on conflict ("uuid_identification") DO UPDATE SET "created_at" = EXCLUDED."created_at"
        """
        cursor.execute(sql_create)
        trace.created_numbers_records = cursor.rowcount
        trace.save()

    return trace


@transaction.atomic
def signboards_invoices_update():
    """Mise à jour des Enseignes pour la facturation"""
    trace_name = "Mise à jour des Enseignes pour la facturation"
    file_name = "insert into ..."
    application_name = "signboards_invoices_update"
    flow_name = "signboards_invoices_update"
    comment = "Mise à jour historique Enseignes pour la facturation"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)

    with connection.cursor() as cursor:
        sql_create = """
        insert into invoices_signboardsinvoices
        (
            "created_at",
            "uuid_identification",
            -- Enseigne
            "code_signboard",
            "logo_signboard",
            "message",
            "email_contact"
        )
        select
            now() as created_at,
            coalesce("isi"."uuid_identification", gen_random_uuid()) as "uuid_identification",
            -- Enseigne
            "cps"."code" as "code_signboard",
            coalesce("cps"."logo", '') as "logo_signboard",
            coalesce("cps"."message", '') as "message",
            coalesce("cps"."email_contact", '') as "email_contact"
        from "centers_purchasing_signboard" "cps"
        left join "invoices_signboardsinvoices" "isi"
        on "isi"."code_signboard" = "cps"."code"
        and coalesce("isi"."logo_signboard", '') = coalesce("cps"."logo", '')
        and coalesce("isi"."message", '') = coalesce("cps"."message", '')
        and coalesce("isi"."email_contact", '') = coalesce("cps"."email_contact", '')
        on conflict ("uuid_identification") DO UPDATE SET "created_at" = EXCLUDED."created_at"
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
        # On met dabord à jour les champs dont on a besoins dans la table centers_clients_maison
        sql_update_ccm = """
        update "centers_clients_maison" "ccm"
        set 
            "invoice_entete" = 	case 
                                    when 
                                        "ccm"."invoice_entete" isnull 
                                        or 
                                        "ccm"."invoice_entete" = '' 
                                    then "ccm"."intitule"
                                    else "ccm"."invoice_entete"
                                end,
            "immeuble" = case 
                    when "ccm"."immeuble" isnull or UPPER("ccm"."immeuble") = 'NONE' 
                    then '' 
                    else "ccm"."immeuble" 
                end,
            "adresse" = case 
                    when "ccm"."adresse" isnull or UPPER("ccm"."adresse") = 'NONE' 
                    then '' 
                    else "ccm"."adresse" 
                end,
            "code_postal" = case 
                    when "ccm"."code_postal" isnull or UPPER("ccm"."code_postal") = 'NONE'
                    then '' 
                    else "ccm"."code_postal" 
                end,
            "ville" = case 
                    when "ccm"."ville" isnull or UPPER("ccm"."ville") = 'NONE'
                    then '' 
                    else "ccm"."ville" 
                end
        """
        cursor.execute(sql_update_ccm)

        # On met dabord à jour les champs dont on a besoins dans la table book_society
        slq_update_bs = """
        update "book_society" "bs"
        set 
            "invoice_entete" = case 
                                when "bs"."invoice_entete" isnull or "bs"."invoice_entete" = '' 
                                then  case when "bs"."name" isnull then '' else "bs"."name" end 
                                else "bs"."invoice_entete"
                              end,
            "immeuble" = case 
                            when "bs"."immeuble" isnull or UPPER("bs"."immeuble") = 'NONE'
                            then '' 
                            else "bs"."immeuble" 
                         end,
            "adresse" = case 
                            when "bs"."adresse" isnull or UPPER("bs"."adresse") = 'NONE'
                            then '' 
                            else "bs"."adresse" 
                        end,
            "code_postal" = case 
                                when "bs"."code_postal" isnull or UPPER("bs"."code_postal") = 'NONE'
                                then '' 
                                else "bs"."code_postal" 
                            end,
            "ville" = case 
                        when "bs"."ville" isnull or UPPER("bs"."ville") = 'NONE'
                        then '' 
                        else "bs"."ville" 
                      end
        """
        cursor.execute(slq_update_bs)

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
            "pays_third_party",
            "payment_condition_client",
            "vat_cee_number_cct",
            "vat_cee_number_client"
        )
        select
            now() as created_at,
            coalesce("isi"."uuid_identification", gen_random_uuid()) as "uuid_identification",
            -- CCT
            "ccm"."cct",
            "ccm"."invoice_entete" as "name_cct", 
            "ccm"."immeuble" as "immeuble_cct",
            "ccm"."adresse" as "adresse_cct",
            "ccm"."code_postal" as "code_postal_cct",
            "ccm"."ville" as "ville_cct",
            "com"."country_name" as "pays_cct",
            -- Tiers facturé à qui appartient le CCT
            "bs"."third_party_num",
            "bs"."invoice_entete" as "name_third_party",
            "bs"."immeuble" "immeuble_third_party",
            "bs"."adresse" as "adresse_third_party",
            "bs"."code_postal" as "code_postal_third_party",
            "bs"."ville" as "ville_third_party",
            coalesce("bsm"."country_name", '') as "pays_third_party",
            coalesce("ap"."name", '') as "payment_condition_client",
            coalesce("ccm"."vat_cee_number", '') as "vat_cee_number_cct",
            coalesce("bs"."vat_cee_number", '') as "vat_cee_number_client"
        from "centers_clients_maison" "ccm"
        left join "book_society" "bs"  
        on "ccm"."third_party_num" = "bs"."third_party_num" 
        left join "countries_country" "com"
        on "com"."country" = "ccm"."pays"
        left join "countries_country" "bsm"
        on "bsm"."country" = "bs"."pays"
        left join "accountancy_paymentcondition" "ap"
        on "ap"."auuid" = "bs"."payment_condition_client"
        left join "invoices_partiesinvoices" "isi"
        on "isi"."cct" = "ccm"."cct"::varchar
        and "isi"."name_cct" = "ccm"."invoice_entete"
        and "isi"."immeuble_cct" = "ccm"."immeuble"
        and "isi"."adresse_cct" = "ccm"."adresse"
        and "isi"."code_postal_cct" = "ccm"."code_postal"
        and "isi"."ville_cct" = "ccm"."ville"
        and "isi"."pays_cct" = "com"."country_name"
        and "isi"."third_party_num" = "bs"."third_party_num"::varchar
        and "isi"."name_third_party" = "bs"."invoice_entete"
        and "isi"."immeuble_third_party" = "bs"."immeuble"
        and "isi"."adresse_third_party" = "bs"."adresse"
        and "isi"."code_postal_third_party" = "bs"."code_postal"
        and "isi"."ville_third_party" = "bs"."ville"
        and "isi"."pays_third_party" = coalesce("bsm"."country_name", '')
        and "isi"."payment_condition_client" = coalesce("ap"."name", '')
        and "isi"."vat_cee_number_cct" = coalesce("ccm"."vat_cee_number", '')
        and "isi"."vat_cee_number_client" = coalesce("bs"."vat_cee_number", '')
        on conflict ("uuid_identification") 
        DO UPDATE SET "created_at" = EXCLUDED."created_at"
        """
        cursor.execute(sql_create)
        trace.created_numbers_records = cursor.rowcount
        trace.save()

    return trace


def process_update():
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
                trace.time_to_process = (timezone.now() - trace.created_at).total_seconds()
                trace.save()


if __name__ == "__main__":
    while True:
        maintenant = datetime.now()
        heure = maintenant.hour
        minute = maintenant.minute

        if heure == 7 and minute == 30:
            print(
                "Mise à jour des CentersInvoices, SignboardsInvoices et PartiesInvoices : ",
                maintenant,
            )
            process_update()

        time.sleep(60)
