"""FR : Vues Django pour l'envoi d'emails avec suivi SSE en temps réel.

EN : Django views for sending emails with real-time SSE tracking.

created at: 2025-01-10
created by: Paulo ALVES
"""

import uuid

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from apps.invoices.bin.api_gmail.tasks_gmail_sse import launch_celery_send_invoice_mails_gmail_sse


@login_required
@require_http_methods(["GET", "POST"])
def send_invoices_emails_sse(request):
    """Page d'envoi des factures par email avec suivi SSE en temps réel.

    GET: Affiche la page avec le formulaire ou la jauge de progression
    POST: Lance l'envoi des factures via Celery et retourne le job_id
    """
    if request.method == "POST":
        # Récupération des paramètres optionnels
        cct = request.POST.get("cct", None)
        period = request.POST.get("period", None)

        # Génère un job_id unique
        job_id = str(uuid.uuid4())

        # Lance la tâche Celery en arrière-plan
        # Le job_id est transmis à la tâche : c'est lui que le navigateur suit en SSE
        launch_celery_send_invoice_mails_gmail_sse.delay(
            user_pk=request.user.pk,
            cct=cct,
            period=period,
            job_id=job_id,
        )

        # Retourne le job_id pour que le frontend puisse suivre la progression
        return JsonResponse(
            {"success": True, "job_id": job_id, "message": "L'envoi des factures a démarré"}
        )

    # GET: Affiche la page avec le formulaire
    return render(request, "invoices/send_invoices_sse.html")


@login_required
@require_http_methods(["GET"])
def send_invoices_progress_sse(request, job_id):
    """Page de progression SSE pour un job spécifique.

    Affiche uniquement la jauge de progression en temps réel.

    :param job_id: UUID du job de progression
    """
    context = {
        "job_id": job_id,
    }

    return render(request, "invoices/send_invoices_progress_sse.html", context)
