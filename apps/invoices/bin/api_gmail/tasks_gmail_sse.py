"""FR : Tâches Celery avec SSE (Server-Sent Events) pour l'API Gmail.

EN : Celery tasks with SSE (Server-Sent Events) for Gmail API.

Commentaire:
Version avec suivi SSE en temps réel pour afficher la progression
dans le navigateur sans polling.

created at: 2025-01-10
created by: Paulo ALVES
"""

import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pendulum
from bs4 import BeautifulSoup
from celery import shared_task
from django.db import connection
from django.db.models import Count
from pydantic import ValidationError

from apps.core.bin.clean_celery import clean_memory
from apps.core.bin.sse_progress import SSEProgressTracker
from apps.core.functions.functions_setups import settings
from apps.core.functions.functions_validations import CheckEmail
from apps.core.models import SSEProgress
from apps.data_flux.trace import get_trace

# Le sender est un objet paresseux : l'authentification Gmail n'a lieu qu'au premier envoi
from apps.invoices.bin.api_gmail.sender import sender
from apps.invoices.models import SaleInvoice
from apps.parameters.models import Email
from apps.users.models import User
from heron.loggers import LOGGER_EMAIL, LOGGER_INVOICES


@dataclass
class _SendJob:
    """État d'un envoi en masse : utilisateur, progression en base, flux SSE et compteurs."""

    user: Any
    progress: Any
    sse: Any
    total: int
    nb_success: int = 0
    nb_errors: int = 0


def _email_context() -> dict:
    """Sujet et corps (html et texte) du mail de facturation."""
    email = Email.objects.get(name=0)

    return {
        "subject_email": str(email.subject),
        "email_html": str(email.email_body),
        "email_text": BeautifulSoup(str(email.email_body), "lxml").get_text(),
    }


def _invoices_to_send(cct: str, period: str):
    """Factures à envoyer, regroupées par cct et fichier de synthèse : celles du cct et de la.

    période demandés, sinon toutes les factures imprimées, non finales et non envoyées.
    """
    if cct and period:
        # Si l'on demande un cct on doit avoir la période pour filtrer
        filters = {"cct": cct, "invoice_month": period, "printed": True, "type_x3__in": (1, 2)}
    else:
        # Envoi de toutes les factures imprimées en pdf et non finales
        filters = {"final": False, "printed": True, "type_x3__in": (1, 2), "send_email": False}

    return (
        SaleInvoice.objects.filter(**filters)
        .values("cct", "global_invoice_file", "invoice_month")
        .annotate(dcount=Count("cct"))
        .order_by("cct")
    )


def _prepare_emails(cct_invoices_list, context_dict: dict) -> tuple[list, list]:
    """Prépare les emails à envoyer et, en parallèle, la correspondance cct / facture de chacun."""
    email_list = []
    cct_invoice_mapping = []

    LOGGER_INVOICES.info("📋 Préparation des emails...")

    for cct_dict in cct_invoices_list:
        invoice_data = prepare_invoice_email_data({**context_dict, **cct_dict})

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

    return email_list, cct_invoice_mapping


def _record_sent(job: _SendJob, i: int, mapping: dict, result) -> None:
    """Email envoyé : facture marquée envoyée, trace de succès, progression et événement SSE."""
    SaleInvoice.objects.filter(
        cct=mapping["cct"],
        global_invoice_file=mapping["global_invoice_file"],
        invoice_month=pendulum.parse(str(mapping["invoice_month"])).date(),
        printed=True,
        type_x3__in=(1, 2),
    ).update(send_email=True)

    trace = get_trace(
        trace_name="Send invoices mail (Gmail API SSE)",
        file_name=str(mapping["file_path"]),
        application_name="invoices_send_by_email_gmail_sse",
        flow_name="send_invoice_email_gmail_sse",
        comment=f"✅ Email envoyé avec succès (ID: {result.message_id})",
    )
    trace.created_by = job.user
    trace.save()

    job.progress.update_progress(processed=1)
    job.sse.send_progress(
        current=i,
        total=job.total,
        message=f"✅ Email {i}/{job.total} envoyé : {mapping['cct']} - {mapping['global_invoice_file']} → {', '.join(mapping['mail_to'][:2])}{'...' if len(mapping['mail_to']) > 2 else ''}",
    )

    LOGGER_INVOICES.info(
        "✅ [%d/%d] Email envoyé : %s - %s",
        i,
        job.total,
        mapping["cct"],
        mapping["global_invoice_file"],
    )


def _record_error(job: _SendJob, i: int, mapping: dict, result) -> None:
    """Email refusé : trace d'erreur, progression en échec et avertissement SSE."""
    trace = get_trace(
        trace_name="Send invoices mail ERROR (Gmail API SSE)",
        file_name=str(mapping["file_path"]),
        application_name="invoices_send_by_email_gmail_sse",
        flow_name="send_invoice_email_gmail_sse",
        comment=f"❌ Erreur lors de l'envoi: {result.error}",
    )
    trace.errors = True
    trace.created_by = job.user
    trace.save()

    job.progress.update_progress(processed=1, failed=1)
    job.sse.send_warning(
        f"⚠️  Email {i}/{job.total} ERREUR : {mapping['cct']} - {mapping['global_invoice_file']} : {result.error}"
    )

    LOGGER_INVOICES.error(
        "❌ [%d/%d] Erreur email : %s - %s : %s",
        i,
        job.total,
        mapping["cct"],
        mapping["global_invoice_file"],
        result.error,
    )


def _send_one(job: _SendJob, i: int, email_data: tuple, mapping: dict) -> None:
    """Envoie un email et enregistre son résultat. L'email n'est compté qu'une fois : en succès dès.

    qu'il est parti (même si l'enregistrement du suivi échoue ensuite), en erreur sinon.
    """
    sent = False

    try:
        mail_to, subject, text, html, context, attachments = email_data
        result = sender.send_message(mail_to, subject, text, html, context, attachments)
        sent = bool(result.success)

        if sent:
            _record_sent(job, i, mapping, result)
        else:
            _record_error(job, i, mapping, result)

    except Exception as error:
        LOGGER_INVOICES.exception(
            "❌ [%d/%d] Exception lors de l'envoi de l'email",
            i,
            job.total,
        )

        if sent:
            job.sse.send_warning(
                f"⚠️  Email {i}/{job.total} envoyé, suivi incomplet : "
                f"{mapping['cct']} - {str(error)[:100]}"
            )
        else:
            job.progress.update_progress(processed=1, failed=1)
            job.sse.send_warning(
                f"⚠️  Email {i}/{job.total} EXCEPTION : {mapping['cct']} - {str(error)[:100]}"
            )

    job.nb_success += sent
    job.nb_errors += not sent


def _send_emails(
    job_id: str, user, email_list: list, cct_invoice_mapping: list, metadata: dict
) -> dict:
    """Envoie les emails avec suivi de progression (base et SSE) et renvoie les statistiques."""
    total = len(email_list)

    # Crée l'objet de progression SSE en DB
    progress = SSEProgress.objects.create(
        job_id=job_id,
        user=user,
        task_type="email_sending",
        total_items=total,
        status="pending",
        metadata=metadata,
    )

    # Crée le tracker SSE pour envoyer les événements temps réel
    job = _SendJob(user=user, progress=progress, sse=SSEProgressTracker(job_id), total=total)

    # Marque comme démarré
    progress.mark_as_started()
    job.sse.send_start(total=total, message=f"Début de l'envoi de {total} facture(s)...")

    # Envoi des emails avec mise à jour SSE en temps réel
    LOGGER_INVOICES.info("📧 Envoi de %d facture(s) via l'API Gmail (job_id: %s)...", total, job_id)

    start_time = time.time()

    for i, (email_data, mapping) in enumerate(
        zip(email_list, cct_invoice_mapping, strict=False), 1
    ):
        _send_one(job, i, email_data, mapping)

    elapsed_time = time.time() - start_time
    average_rate = total / elapsed_time if elapsed_time > 0 else 0

    # Marque la progression comme terminée
    progress.mark_as_completed()
    job.sse.send_complete(
        total=total,
        message=f"✅ Envoi terminé : {job.nb_success} succès, {job.nb_errors} erreur(s) sur {total} facture(s) ({elapsed_time:.1f}s, {average_rate:.1f} emails/s)",
    )

    LOGGER_INVOICES.info(
        "🎉 Envoi terminé (job_id: %s): %d succès, %d erreur(s) sur %d email(s) "
        "(temps total: %.1fs, moyenne: %.1f emails/s)",
        job_id,
        job.nb_success,
        job.nb_errors,
        total,
        elapsed_time,
        average_rate,
    )

    return {
        "success": True,
        "sent": job.nb_success,
        "errors": job.nb_errors,
        "total": total,
        "job_id": job_id,
        "elapsed_time": elapsed_time,
    }


def _report_failure(job_id: str, error: Exception) -> None:
    """Marque le job en échec en base et envoie l'événement SSE d'erreur."""
    try:
        progress = SSEProgress.objects.get(job_id=job_id)
        progress.mark_as_failed(str(error))

        sse = SSEProgressTracker(job_id)
        sse.send_error(f"❌ Erreur critique : {error!s}")
    except Exception:
        LOGGER_EMAIL.exception("Impossible de signaler l'échec du job %s", job_id)


@shared_task(name="celery_send_invoices_emails_gmail_sse")
@clean_memory
def launch_celery_send_invoice_mails_gmail_sse(
    user_pk: str, cct: str | None = None, period: str | None = None, job_id: str | None = None
):
    """Main pour lancement de l'envoi des factures par mails via l'API Gmail.

    avec suivi SSE en temps réel
    :param user_pk: pk de l'utilisateur qui a lancé le process
    :param cct: cct de la facture à envoyer
    :param period: période de la facturation
    :param job_id: identifiant du job transmis par la vue (sinon généré)
    :return: dict avec job_id et statistiques.
    """
    job_id = job_id or str(uuid.uuid4())

    LOGGER_INVOICES.info(
        "🚀 Début de l'envoi des factures par email via l'API Gmail SSE "
        "(job_id: %s, utilisateur: %s, cct: %s, période: %s)",
        job_id,
        user_pk,
        cct,
        period,
    )

    try:
        user = User.objects.get(pk=user_pk)
        context_dict = _email_context()
        email_list, cct_invoice_mapping = _prepare_emails(
            _invoices_to_send(cct or "", period or ""), context_dict
        )

        if not email_list:
            LOGGER_INVOICES.warning("⚠️  Aucun email à envoyer")
            return {"success": True, "sent": 0, "errors": 0, "job_id": job_id}

        metadata = {"cct": cct or "Tous", "period": period or "Toutes"}

        return _send_emails(job_id, user, email_list, cct_invoice_mapping, metadata)

    except Exception as error:
        LOGGER_INVOICES.exception(
            "❌ Erreur GLOBALE lors de l'envoi des factures via l'API Gmail SSE (job_id: %s)",
            job_id,
        )

        # Marque comme failed en DB et envoie événement SSE d'erreur
        _report_failure(job_id, error)

        return {"success": False, "error": str(error), "job_id": job_id}


def prepare_invoice_email_data(context_dict: dict):
    """Prépare les données pour l'envoi d'une facture par email.

    :param context_dict: Dictionnaire des éléments pour l'envoi d'emails
    :return: Dictionnaire avec les données préparées ou None si erreur.
    """
    file_path = Path(settings.SALES_INVOICES_FILES_DIR) / context_dict["global_invoice_file"]

    if not file_path.exists():
        LOGGER_EMAIL.error("❌ Fichier non trouvé: %s", file_path)
        return None

    context_email = {
        "periode": (
            pendulum.parse(str(context_dict.get("invoice_month")))
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
                    f'<p style="padding: 0;margin: 0 0 10px 0;font-size: 11pt;">{synthese}</p>'
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
                f'<p style="padding: 0;margin: 0 0 10px 0;font-size: 11pt;">{invoice}</p>'
            )

    mail_to_list = [mail for mail in mail_to_list if mail]

    if not mail_to_list:
        LOGGER_EMAIL.warning(
            "⚠️  Pas d'adresses mail valides pour le client : %s",
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
