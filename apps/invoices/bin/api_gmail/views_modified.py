# pylint: disable=E0401
"""
FR : Vue modifiée pour l'envoi des factures avec suivi de progression
EN : Modified view for invoice sending with progress tracking

Commentaire:
Cette vue remplace ou complète la vue send_email_pdf_invoice existante
pour ajouter le suivi de progression en temps réel.

created at: 2025-01-10
created by: Paulo ALVES 
"""

import uuid
from django.shortcuts import render
from django.contrib import messages
from django.db.models import Count
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from heron import celery_app
from apps.invoices.bin.generate_invoices_pdf import get_invoices_in_progress
from apps.invoices.bin.pre_controls import control_emails
from apps.invoices.models import SaleInvoice

# Import conditionnel
try:
    from .models_progress import EmailSendProgress
    PROGRESS_TRACKING_ENABLED = True
except ImportError:
    PROGRESS_TRACKING_ENABLED = False
    EmailSendProgress = None


def send_email_pdf_invoice_with_progress(request):
    """
    Vue d'envoi de toutes les factures pdf, par mail avec suivi de progression
    Compatible avec l'ancienne vue mais ajoute le suivi de progression
    """

    if request.method == "POST" and "email_essais" in request.POST:
        from django.shortcuts import redirect, reverse
        return redirect(reverse("invoices:send_email_essais"))

    titre_table = "Envoi Global, par mail des factures de vente"

    # On contrôle qu'il y ait des emails à envoyer
    emails_to_send = control_emails()

    if not emails_to_send:
        request.session["level"] = 50
        messages.add_message(request, 50, "Il n'y a aucune facture pdf à envoyer !")
        context = {"margin_table": 50, "titre_table": titre_table, "not_finalize": True}
        return render(request, "invoices/send_email_invoices.html", context=context)

    # On contrôle qu'il y ait des pdf à envoyer par mail
    sales_invoices_exists = SaleInvoice.objects.filter(
        final=False, send_email=False, type_x3__in=(1, 2), printed=True
    ).exists()

    context = {
        "margin_table": 50,
        "titre_table": titre_table,
        "news": sales_invoices_exists,
    }

    if not sales_invoices_exists:
        request.session["level"] = 50
        messages.add_message(request, 50, "Il n'y a aucune facture pdf à envoyer !")
        context["en_cours"] = False
        return render(request, "invoices/send_email_invoices.html", context=context)

    insertion, pdf_invoices, email_invoices = get_invoices_in_progress()

    # Si l'on envoie un POST alors, on lance l'envoi en tâche de fond celery
    if all(
        [request.method == "POST", not insertion, not pdf_invoices, not email_invoices]
    ):
        # Génère un job_id unique
        job_id = str(uuid.uuid4())

        user_pk = request.user.pk

        # Lance la tâche Celery avec progression
        celery_app.signature(
            "celery_send_invoices_emails_gmail_with_progress",
            kwargs={"user_pk": str(user_pk), "job_id": job_id},
        ).apply_async()

        email_invoices = True

        # Si c'est une requête AJAX, retourne du JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                "success": True,
                "job_id": job_id,
                "message": "Envoi lancé avec succès",
            })

    if insertion:
        titre_table = "INSERTION DES FACTURES EN COURS, VEUILLEZ REESSSAYEZ PLUS TARD !"

    if pdf_invoices:
        titre_table = (
            "GENERATION DES PDF EN COURS, VEUILLEZ REESSSAYEZ PLUS TARD ! "
            "(N'OUBLIEZ PAS DE REGARDER LES TRACES APRES LA GENERATION)"
        )

    if email_invoices:
        titre_table = "LES FACTURES SONT EN COURS D'ENVOI PAR MAIL !"

    context["en_cours"] = any([insertion, pdf_invoices, email_invoices])
    context["titre_table"] = titre_table

    # Ajoute le job_id actif s'il existe
    if PROGRESS_TRACKING_ENABLED and EmailSendProgress:
        active_progress = EmailSendProgress.objects.filter(
            user=request.user,
            status__in=["pending", "in_progress"]
        ).first()

        if active_progress:
            context["active_job_id"] = active_progress.job_id

    return render(request, "invoices/send_email_invoices.html", context=context)


@require_http_methods(["GET"])
def count_emails_to_send(request):
    """
    API pour compter le nombre d'emails à envoyer
    :param request: Request Django
    :return: JsonResponse avec le nombre d'emails
    """
    try:
        # Compte les factures à envoyer
        count = SaleInvoice.objects.filter(
            final=False,
            printed=True,
            type_x3__in=(1, 2),
            send_email=False,
        ).values("cct", "global_invoice_file", "invoice_month") \
         .annotate(dcount=Count("cct")) \
         .count()

        return JsonResponse({
            "success": True,
            "count": count,
        })

    except Exception as error:
        return JsonResponse({
            "success": False,
            "error": str(error),
        }, status=500)