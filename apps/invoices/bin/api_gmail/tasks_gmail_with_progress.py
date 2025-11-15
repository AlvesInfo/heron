# pylint: disable=E0401,W0718,E0633,W1203,W1201,C0411
"""
FR : Tâches Celery avec suivi de progression pour l'API Gmail
EN : Celery tasks with progress tracking for Gmail API

Commentaire:
Version améliorée des tâches Celery qui met à jour la progression
en temps réel dans la base de données pour affichage dans l'interface.

created at: 2025-01-10
created by: Paulo ALVES 
"""

import time
import uuid
from typing import AnyStr, Dict

import pendulum
from celery import shared_task
from django.db.models import Count
from bs4 import BeautifulSoup

from heron.loggers import LOGGER_INVOICES, LOGGER_EMAIL
from apps.users.models import User
from apps.data_flux.trace import get_trace
from apps.invoices.models import SaleInvoice
from apps.parameters.models import Email
from apps.core.functions.functions_setups import settings
from pathlib import Path

from .sender import sender

# Import conditionnel du modèle de progression
try:
    from .models_progress import EmailSendProgress

    PROGRESS_TRACKING_ENABLED = True
except ImportError:
    LOGGER_INVOICES.warning(
        "Le modèle EmailSendProgress n'est pas disponible. "
        "La progression ne sera pas suivie."
    )
    PROGRESS_TRACKING_ENABLED = False
    EmailSendProgress = None


# @shared_task(name="celery_send_invoices_emails_gmail_with_progress")
def launch_celery_send_invoice_mails_gmail_with_progress(
    user_pk: AnyStr, cct: AnyStr = None, period: AnyStr = None, job_id: AnyStr = None
):
    """
    Main pour lancement de l'envoi des factures par mails via l'API Gmail
    avec suivi de progression en temps réel
    :param user_pk: pk de l'utilisateur qui a lancé le process
    :param cct: cct de la facture à envoyer
    :param period: période de la facturation
    :param job_id: ID du job de progression (généré automatiquement si non fourni)
    """
    # Génère un job_id si non fourni
    if not job_id:
        job_id = str(uuid.uuid4())

    LOGGER_INVOICES.info(
        "Début de l'envoi des factures par email via l'API Gmail "
        "(job_id: %s, utilisateur: %s, cct: %s, période: %s)",
        job_id,
        user_pk,
        cct,
        period,
    )

    # Crée l'objet de progression
    progress = None
    if PROGRESS_TRACKING_ENABLED:
        try:
            user = User.objects.get(pk=user_pk)
            progress = EmailSendProgress.objects.create(
                job_id=job_id,
                user=user,
                status="pending",
                cct=cct or "Tous",
                period=period or "Toutes",
            )
        except Exception as error:
            LOGGER_INVOICES.error(
                "Erreur lors de la création de la progression: %s", error
            )

    try:
        # Récupération du texte du corps de mail et sujet
        email = Email.objects.get(name=0)
        context_dict = {
            "subject_email": str(email.subject),
            "email_html": str(email.email_body),
            "email_text": BeautifulSoup(str(email.email_body), "lxml").get_text(),
        }

        # Si l'on demande un cct on doit avoir la période pour filtrer
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
            # Envoi de toutes les factures imprimées en pdf et non finales
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
        cct_invoice_mapping = []

        if progress:
            progress.current_operation = "Préparation des emails..."
            progress.save()

        for cct_dict in cct_invoices_list:
            invoice_context = {**context_dict, **cct_dict}
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
            if progress:
                progress.mark_as_completed()
            return {"success": True, "sent": 0, "errors": 0, "job_id": job_id}

        # Met à jour la progression avec le nombre total
        if progress:
            progress.total_emails = len(email_list)
            progress.mark_as_started()
            progress.current_operation = f"Envoi de {len(email_list)} factures..."
            progress.save()

        # Envoi des emails avec mise à jour de la progression
        LOGGER_INVOICES.info(
            "Envoi de %d factures via l'API Gmail (job_id: %s)...",
            len(email_list),
            job_id,
        )

        nb_success = 0
        nb_errors = 0
        start_time = time.time()

        for i, (email_data, mapping) in enumerate(
            zip(email_list, cct_invoice_mapping), 1
        ):
            try:
                mail_to, subject, text, html, context, attachments = email_data

                # Envoie l'email
                result = sender.send_message(
                    mail_to, subject, text, html, context, attachments
                )

                if result.success:
                    nb_success += 1

                    # Marque la facture comme envoyée
                    SaleInvoice.objects.filter(
                        cct=mapping["cct"],
                        global_invoice_file=mapping["global_invoice_file"],
                        invoice_month=pendulum.parse(
                            str(mapping["invoice_month"])
                        ).date(),
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

                    # Met à jour la progression
                    if progress:
                        progress.update_progress(
                            sent=1,
                            failed=0,
                            current_operation=f"Envoyé {i}/{len(email_list)}: {mapping['global_invoice_file']}",
                        )

                else:
                    nb_errors += 1

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

                    # Met à jour la progression
                    if progress:
                        progress.update_progress(
                            sent=1,
                            failed=1,
                            current_operation=f"Erreur {i}/{len(email_list)}: {mapping['global_invoice_file']}",
                        )

            except Exception as error:
                nb_errors += 1
                LOGGER_INVOICES.exception("Erreur lors de l'envoi de l'email %d: %s", i, error)

                if progress:
                    progress.update_progress(
                        sent=1,
                        failed=1,
                        current_operation=f"Erreur {i}/{len(email_list)}: {str(error)}",
                    )

        elapsed_time = time.time() - start_time
        average_rate = len(email_list) / elapsed_time if elapsed_time > 0 else 0

        LOGGER_INVOICES.info(
            "Envoi terminé (job_id: %s): %d succès, %d erreurs sur %d emails "
            "(temps total: %.1fs, moyenne: %.1f emails/s)",
            job_id,
            nb_success,
            nb_errors,
            len(email_list),
            elapsed_time,
            average_rate,
        )

        # Marque la progression comme terminée
        if progress:
            progress.mark_as_completed()

        return {
            "success": True,
            "sent": nb_success,
            "errors": nb_errors,
            "total": len(email_list),
            "job_id": job_id,
        }

    except Exception as error:
        LOGGER_INVOICES.exception(
            "Erreur lors de l'envoi des factures via l'API Gmail (job_id: %s): %s",
            job_id,
            error,
        )

        if progress:
            progress.mark_as_failed(str(error))

        return {"success": False, "error": str(error), "job_id": job_id}


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

    mail_to_list = [mail for mail in mail_to_list if mail]

    if not mail_to_list:
        LOGGER_EMAIL.warning(
            "Pas d'adresses mail valides pour le client : %s",
            context_email.get("cct"),
        )
        return None

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