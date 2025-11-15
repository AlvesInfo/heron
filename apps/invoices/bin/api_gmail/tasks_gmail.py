# pylint: disable=E0401,W0718,E0633,W1203,W1201,C0411
"""
FR : Tâches Celery pour l'envoi des factures via l'API Gmail
EN : Celery tasks for sending invoices via Gmail API

Commentaire:
Ce module contient les tâches Celery pour envoyer les factures
par email en utilisant l'API Gmail au lieu de SMTP.

Avantages par rapport à SMTP:
- Pas de limite de connexion
- Meilleure gestion des quotas
- Retry automatique intégré
- Moins d'erreurs de connexion

created at: 2025-01-10
created by: Paulo ALVES 
"""

import time
from typing import AnyStr, Dict

import pendulum
from celery import shared_task
from django.db.models import Count
from bs4 import BeautifulSoup

from heron.loggers import LOGGER_INVOICES, LOGGER_EMAIL
from apps.core.bin.clean_celery import clean_memory
from apps.users.models import User
from apps.data_flux.trace import get_trace
from apps.invoices.models import SaleInvoice
from apps.parameters.models import Email
from apps.core.functions.functions_setups import settings
from pathlib import Path

from .sender import sender


# @shared_task(name="celery_send_invoices_emails_gmail")
def launch_celery_send_invoice_mails_gmail(
    user_pk: AnyStr, cct: AnyStr = None, period: AnyStr = None
):
    """
    Main pour lancement de l'envoi des factures par mails via l'API Gmail
    :param user_pk: pk de l'utilisateur qui a lancé le process
    :param cct: cct de la facture à envoyer
    :param period: période de la facturation
    """
    LOGGER_INVOICES.info(
        "Début de l'envoi des factures par email via l'API Gmail "
        "(utilisateur: %s, cct: %s, période: %s)",
        user_pk,
        cct,
        period,
    )

    # Récupération du texte du corps de mail et sujet
    email = Email.objects.get(name=0)
    context_dict = {
        "subject_email": str(email.subject),
        "email_html": str(email.email_body),
        "email_text": BeautifulSoup(str(email.email_body), "lxml").get_text(),
    }

    # Si l'on demande un cct on doit avoir la période pour filtrer et ne pas tout envoyer
    if cct and period:
        cct_invoices_list = (
            SaleInvoice.objects.filter(
                cct=cct,
                invoice_month=period,
                printed=True,
                type_x3__in=(1, 2),
            )
            .values("cct", "global_invoice_file", "invoice_month")
            .annotate(dcount=Count("cct"))
            .order_by("cct")
        )
    else:
        # Envoi de toutes les factures imprimées en pdf et non finales, et non envoyées
        cct_invoices_list = (
            SaleInvoice.objects.filter(
                final=False,
                printed=True,
                type_x3__in=(1, 2),
                send_email=False,
            )
            .values("cct", "global_invoice_file", "invoice_month")
            .annotate(dcount=Count("cct"))
            .order_by("cct")
        )

    # Prépare la liste des emails à envoyer
    email_list = []
    cct_invoice_mapping = []  # Pour mapper les résultats aux factures

    for cct_dict in cct_invoices_list:
        invoice_context = {**context_dict, **cct_dict}

        # Récupère les informations de la facture
        invoice_data = prepare_invoice_email_data(invoice_context)

        if invoice_data:
            email_list.append(invoice_data["email_tuple"])
            cct_invoice_mapping.append(
                {
                    "cct": cct_dict["cct"],
                    "global_invoice_file": cct_dict["global_invoice_file"],
                    "invoice_month": cct_dict["invoice_month"],
                    "mail_to": invoice_data["mail_to"],
                    "file_path": invoice_data["file_path"],
                }
            )

    if not email_list:
        LOGGER_INVOICES.warning("Aucun email à envoyer")
        return {"success": True, "sent": 0, "errors": 0}

    try:
        # Envoi en masse via l'API Gmail
        LOGGER_INVOICES.info(
            "Envoi de %d factures via l'API Gmail...", len(email_list)
        )
        nb_success, nb_errors, results = sender.send_mass_mail(email_list)

        # Mise à jour des factures envoyées avec succès
        for i, result in enumerate(results):
            if result.success and i < len(cct_invoice_mapping):
                mapping = cct_invoice_mapping[i]

                # Marque la facture comme envoyée
                SaleInvoice.objects.filter(
                    cct=mapping["cct"],
                    global_invoice_file=mapping["global_invoice_file"],
                    invoice_month=pendulum.parse(str(mapping["invoice_month"])).date(),
                    printed=True,
                    type_x3__in=(1, 2),
                ).update(send_email=True)

                # Crée une trace de succès
                trace = get_trace(
                    trace_name="Send invoices mail (Gmail API)",
                    file_name=str(mapping["file_path"]),
                    application_name="invoices_send_by_email_gmail",
                    flow_name="send_invoice_email_gmail",
                    comment=f"Email envoyé avec succès (ID: {result.message_id})",
                )
                trace.created_by = User.objects.get(pk=user_pk)
                trace.save()

                LOGGER_INVOICES.info(
                    "Facture %s envoyée avec succès à %s",
                    mapping["global_invoice_file"],
                    result.recipient,
                )

            elif not result.success and i < len(cct_invoice_mapping):
                mapping = cct_invoice_mapping[i]

                # Crée une trace d'erreur
                trace = get_trace(
                    trace_name="Send invoices mail ERROR (Gmail API)",
                    file_name=str(mapping["file_path"]),
                    application_name="invoices_send_by_email_gmail",
                    flow_name="send_invoice_email_gmail",
                    comment=f"Erreur lors de l'envoi: {result.error}",
                )
                trace.errors = True
                trace.created_by = User.objects.get(pk=user_pk)
                trace.save()

                LOGGER_INVOICES.error(
                    "Erreur lors de l'envoi de la facture %s: %s",
                    mapping["global_invoice_file"],
                    result.error,
                )

        LOGGER_INVOICES.info(
            "Envoi terminé: %d succès, %d erreurs sur %d emails",
            nb_success,
            nb_errors,
            len(email_list),
        )

        return {
            "success": True,
            "sent": nb_success,
            "errors": nb_errors,
            "total": len(email_list),
        }

    except Exception as error:
        LOGGER_INVOICES.exception(
            "Erreur lors de l'envoi des factures via l'API Gmail: %s", error
        )
        return {"success": False, "error": str(error)}


def prepare_invoice_email_data(context_dict: Dict):
    """
    Prépare les données pour l'envoi d'une facture par email
    :param context_dict: Dictionnaire des éléments pour l'envoi d'emails
    :return: Dictionnaire avec les données préparées ou None si erreur
    """
    from django.db import connection
    from apps.core.functions.functions_validations import CheckEmail
    from pydantic.error_wrappers import ValidationError

    file_path = Path(settings.SALES_INVOICES_FILES_DIR) / context_dict.get(
        "global_invoice_file"
    )

    if not file_path.exists():
        LOGGER_EMAIL.error("Fichier non trouvé: %s", file_path)
        return None

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
            "bs"."email_05",
            "cm"."email" as "email_06"
        from "invoices_saleinvoice" "si"
        join "invoices_partiesinvoices" "ip"
          on "si"."parties" = "ip"."uuid_identification"
        join "invoices_centersinvoices" "ic"
          on "si"."centers" = "ic"."uuid_identification"
        join "centers_clients_maison" "cm"
          on "ip"."cct" = "cm"."cct"
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
                email_06,
            ) = row

            if i == 0:
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
                f'<p style="padding: 0;margin: 0 0 10px 0;font-size: 11pt;">'
                f"{invoice}</p>"
            )

    # Filtre les emails vides
    mail_to_list = [mail for mail in mail_to_list if mail]

    if not mail_to_list:
        LOGGER_EMAIL.warning(
            "Pas d'adresses mail valides pour le client : %s",
            context_email.get("cct"),
        )
        return None

    # Prépare le tuple pour l'envoi
    email_tuple = (
        mail_to_list,
        context_dict.get("subject_email"),
        context_dict.get("email_text"),
        context_dict.get("email_html"),
        context_email,
        [file_path],
    )

    return {
        "email_tuple": email_tuple,
        "mail_to": mail_to_list,
        "file_path": file_path,
    }


@shared_task(name="send_invoice_email_gmail")
@clean_memory
def send_invoice_email_gmail(context_dict: Dict, user_pk: int):
    """
    Envoi d'une seule facture par mail via l'API Gmail
    Cette tâche peut être utilisée pour envoyer une facture individuelle
    :param context_dict: dictionnaire des éléments pour l'envoi d'emails
    :param user_pk: pk de l'utilisateur qui a lancé le process
    """
    start_initial = time.time()

    error = False
    trace = None
    to_print = ""

    try:
        # Prépare les données de l'email
        invoice_data = prepare_invoice_email_data(context_dict)

        if not invoice_data:
            error = True
            to_print = (
                f"Pas de données valides pour l'email : "
                f"{context_dict.get('global_invoice_file')}"
            )
        else:
            # Envoi de l'email
            mail_to, subject, text, html, context, attachments = invoice_data[
                "email_tuple"
            ]

            result = sender.send_message(
                mail_to, subject, text, html, context, attachments
            )

            file_path = invoice_data["file_path"]

            if result.success:
                # Marque la facture comme envoyée
                SaleInvoice.objects.filter(
                    cct=context_dict.get("cct"),
                    global_invoice_file=context_dict.get("global_invoice_file"),
                    invoice_month=pendulum.parse(
                        context_dict.get("invoice_month")
                    ).date(),
                    printed=True,
                    type_x3__in=(1, 2),
                ).update(send_email=True)

                trace = get_trace(
                    trace_name="Send invoices mail (Gmail API)",
                    file_name=str(file_path),
                    application_name="invoices_send_by_email_gmail",
                    flow_name="send_invoice_email_gmail",
                    comment=f"Email envoyé avec succès (ID: {result.message_id})",
                )
                to_print = f"Have send invoice email: {file_path.name} - "
            else:
                error = True
                trace = get_trace(
                    trace_name="Send invoices mail ERROR (Gmail API)",
                    file_name=str(file_path),
                    application_name="invoices_send_by_email_gmail",
                    flow_name="send_invoice_email_gmail",
                    comment=f"Erreur lors de l'envoi: {result.error}",
                )
                trace.errors = True
                to_print = (
                    f"Error - Have Not send invoice email !: {file_path.name} - "
                )

            trace.created_by = User.objects.get(pk=user_pk)

    except Exception as except_error:
        error = True
        LOGGER_INVOICES.exception(
            f"Exception Générale: send_invoice_email_gmail : "
            f"{context_dict.get('cct')}\n{except_error!r}"
        )

    finally:
        if trace is not None:
            trace.time_to_process = time.time() - start_initial
            trace.save()

    LOGGER_INVOICES.warning(
        to_print
        + (
            f"Envoi de la facture par mail {context_dict.get('cct')} "
            f": {time.time() - start_initial} s "
        )
    )

    return {
        "Envoi de la facture par mail : ": (
            f"cct : {str(context_dict.get('cct'))} "
            f"- {time.time() - start_initial} s"
        )
    }