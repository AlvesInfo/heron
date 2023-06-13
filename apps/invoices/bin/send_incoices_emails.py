# pylint: disable=E0401,E1101,C0303,R0913
"""
FR : Module d'envoi des factures par email
EN : Send invoices by email module
Commentaire:

created at: 2023-06-13
created by: Paulo ALVES

modified at: 2023-06-13
modified by: Paulo ALVES
"""
import os
import sys
import platform
from pathlib import Path
from typing import Dict

import django

BASE_DIR = r"/"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")

django.setup()

from django.conf import settings
from django.db import connection
import pendulum

from heron.loggers import LOGGER_EMAIL
from apps.data_flux.trace import get_trace
from apps.core.bin.emails import send_mass_mail


def invoices_send_by_email(context_dict: Dict):
    """
    Envoi d'une facture par mail
    :param context_dict: dictionnaire des éléments pour l'envoi d'emails

    CCT	    Période	    Synthèse	Factures	Service	    Centrale Fille
    {0}	    {1}	        {2}	        {3}	        {4}	        {5}
    """
    file_path = Path(settings.SALES_INVOICES_FILES_DIR) / context_dict.get("global_invoice_file")
    print("file_path : ", file_path.name, file_path.is_file())
    error = False
    trace = get_trace(
        trace_name="Send invoices mail",
        file_name=str(file_path),
        application_name="invoices_send_by_email",
        flow_name="send_invoice_email",
        comment="",
    )
    to_print = ""
    context_email = {
        "periode": (
            pendulum.parse(context_dict.get("invoice_month"))
            .format("MMMM YYYY", locale="fr")
            .upper()
        ),
        "factures": "",
    }
    mail_to_list = []

    with connection.cursor() as cursor:
        sql_context = """
        select 
            "si"."cct" || ' - ' || "ip"."name_cct" as "cct_name", 
            'Synthèse : ' || "si"."global_invoice_file" as "synthese",
            (
                '- Facture de ' 
                || 
                "si"."big_category" 
                || 
                ' N°: '  
                || 
                "si"."invoice_sage_number"
            ) as "invoice",
            'Service Comptabilité' as "service",
            'Centrale : '  || "cp"."name" as "center",
            "bs"."email_01",
            "bs"."email_02",
            "bs"."email_03",
            "bs"."email_04",
            "bs"."email_05"
        from "invoices_saleinvoice" "si" 
        join "invoices_partiesinvoices" "ip"
          on "si"."parties" = "ip"."uuid_identification"
        join "invoices_centersinvoices" "ic"
          on "si"."centers" = "ic"."uuid_identification"
        left join "centers_purchasing_childcenterpurchase" "cp"
        on "ic"."code_center" = "cp"."code"  
        left join "book_society" "bs"
          on "ip"."third_party_num" = "bs"."third_party_num"  
        where "si"."cct"= %(cct)s
          and "si"."global_invoice_file" = %(global_invoice_file)s
          and "si"."invoice_month" = %(invoice_month)s
        """
        cursor.execute(sql_context, context_dict)
        for i, row in enumerate(cursor.fetchall()):
            (
                cct_name,
                synthese,
                invoice,
                service,
                center,
                email_01,
                email_02,
                email_03,
                email_04,
                email_05,
            ) = row
            if i == 0:
                context_email["cct"] = cct_name
                context_email["synthese"] = f'<p style="margin-left: 40px;padding-top: 0">{synthese}</p>'
                context_email["service"] = service
                context_email["centrale"] = center
                mail_to_list.append(email_01)
                mail_to_list.append(email_02)
                mail_to_list.append(email_03)
                mail_to_list.append(email_04)
                mail_to_list.append(email_05)

            context_email["factures"] += (
                f'<p style="margin-left: 80px;padding-top: 0;padding-bottom: 20px;">{invoice}</p>'
            )

        mail_to_list = [mail for mail in mail_to_list if mail]
        send_mass_mail(
            [
                (
                    ["paulo@alves.ovh"],
                    context_dict.get("subject_email"),
                    context_dict.get("email_text"),
                    context_dict.get("email_html"),
                    context_email,
                    [
                        file_path,
                    ],
                )
            ]
        )

    try:
        trace.file_name = f"send email invoice : {file_path.name}"
        to_print = f"Have send invoice email : {file_path.name} - "

    except Exception as except_error:
        error = True
        LOGGER_EMAIL.exception(f"Exception Générale : {except_error!r}")

    finally:
        if error:
            trace.errors = True
            trace.comment = (
                trace.comment + "\n. Une erreur c'est produite veuillez consulter les logs"
            )

        trace.save()

    return trace, to_print
