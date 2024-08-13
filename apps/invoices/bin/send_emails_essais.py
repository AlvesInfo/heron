# pylint: disable=E0401,E1101,C0303,R0913,C0413,R0914,W0718,W1203,R0915
# ruff: noqa: E402
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
import time
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
import pendulum
from pydantic.error_wrappers import ValidationError

from heron.loggers import LOGGER_EMAIL
from apps.core.functions.functions_validations import CheckEmail
from apps.core.exceptions import EmailException
from apps.data_flux.trace import get_trace
from apps.core.bin.emails import send_mass_mail
from apps.invoices.models import SaleInvoice


def essais_send_by_email(server, context_dict: Dict):
    """
    Envoi d'une facture par mail
    :param server: server de mail
    :param context_dict: dictionnaire des éléments pour l'envoi d'emails

    CCT	    Période	    Synthèse	Factures	Service	    Centrale Fille
    {0}	    {1}	        {2}	        {3}	        {4}	        {5}
    """
    start = time.time()
    file_path = Path(settings.SALES_INVOICES_FILES_DIR) / "un.pdf"
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
        "factures": "facttures",
    }
    mail_to_list = []
    email = context_dict.get("email_list")

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
        email_06,
    ) = [
        "cct",
        "synthèse",
        "invoice",
        "service",
        "center",
        email,
        "",
        None,
        "test1",
        "test1",
        "aaa"
    ]

    context_email["cct"] = cct_name
    context_email["synthese"] = (
        f"<p "
        f'style="'
        f"padding: 0;"
        f"margin: 0 0 10px 0;"
        f'font-size: 11pt;">{synthese}</p>'
    )
    context_email["service"] = service
    context_email["centrale"] = center

    for email in [
        email_01,
        email_02,
        email_03,
        email_04,
        email_05,
        email_06,
    ]:
        try:
            CheckEmail(email=email)
            mail_to_list.append(email)
        except ValidationError:
            pass

    context_email["factures"] += (
        f'<p style="padding: 0;margin: 0 0 10px 0;font-size: 11pt;">' f"{invoice}</p>"
    )

    try:
        print(mail_to_list)
        if mail_to_list:
            send_mass_mail(
                server,
                [
                    (
                        mail_to_list,
                        context_dict.get("subject_email"),
                        context_dict.get("email_text"),
                        context_dict.get("email_html"),
                        context_email,
                        [
                            file_path,
                        ],
                    )
                ],
            )
            trace.file_name = f"send email invoice : {file_path.name}"
            to_print = f"Have send invoice email : {file_path.name} - "

        else:
            error = True
            trace.comment = f"Pas d'adresses mail pour le client : {context_email.get('ctt')}"
            trace.file_name = f"Send email invoice : {file_path.name}"
            to_print = f"Error - Have Not send invoice email !: {file_path.name} - "

    except EmailException as except_error:
        error = True
        LOGGER_EMAIL.exception(f"Exception EmailException : {str(mail_to_list)}{except_error!r}")

    except Exception as except_error:
        error = True
        LOGGER_EMAIL.exception(f"Exception Générale : {except_error!r}")

    finally:
        if error:
            trace.errors = True
            trace.comment += (
                trace.comment
                + "\n. Une erreur c'est produite veuillez consulter les logs"
                + str(context_dict)
            )
        else:
            # S'il n'y a pas eu d'erreurs ont flag send_mail à true pour ne pas le renvoyer
            SaleInvoice.objects.filter(
                cct=context_dict.get("cct"),
                global_invoice_file=context_dict.get("global_invoice_file"),
                invoice_month=pendulum.parse(context_dict.get("invoice_month")).date(),
                printed=True,
                type_x3__in=(1, 2),
            ).update(send_email=True)

        trace.time_to_process = start - time.time()
        trace.save()

    return trace, to_print
