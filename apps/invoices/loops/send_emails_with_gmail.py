from typing import AnyStr
import time

from celery import group
from django.db import transaction, close_old_connections

from heron import celery_app
from heron.loggers import LOGGER_EMAIL
from apps.users.models import User
from apps.core.models import SSEProgress
from apps.parameters.bin.core import get_action
from apps.parameters.models import ActionInProgress


def send_invoices_emails_gmail(user: int, job_id: str):
    """Envoi en masse des emails par gmail"""
    result = ""
    info = ""
    progress = None

    # S'assurer que l'objet ActionInProgress existe
    get_action(action="send_mass_mail")

    # 1. Marque l'action comme en cours (transaction courte, commitée immédiatement)
    with transaction.atomic():
        active_action = ActionInProgress.objects.select_for_update().get(
            action="send_mass_mail"
        )
        active_action.in_progress = True
        active_action.save()

    # 2. Exécution de la tâche Celery EN DEHORS de la transaction
    try:
        progress = SSEProgress.objects.get(job_id=job_id)

        start_all = time.time()

        # On regroupe les tâches celery à lancer
        result = group(
            *[
                celery_app.signature(
                    "celery_send_invoices_emails_gmail",
                    kwargs={
                        "user_pk": str(user),
                        "job_id": job_id,
                    },
                )
            ]
        )().get(3600)
        LOGGER_EMAIL.warning(f"result : {result!r},\nin {time.time() - start_all} s")

        # Marquer comme terminé, mais avant rafraîchir pour avoir les dernières valeurs
        progress.refresh_from_db()
        progress.mark_as_completed()

    except Exception as error:
        LOGGER_EMAIL.exception(
            "Erreur détectée dans "
            "apps.invoices.loops.send_emails_with_gmail.send_invoices_emails_gmail()"
        )
        # Marquer comme échoué
        try:
            if job_id and not progress:
                progress = SSEProgress.objects.get(job_id=job_id)
            if progress:
                progress.mark_as_failed(str(error))
        except Exception as e:
            LOGGER_EMAIL.error(
                f"Impossible de marquer le SSEProgress comme failed: {e}"
            )

    finally:
        # 3. Remet l'action en cours à False (transaction courte, toujours exécutée)
        with transaction.atomic():
            active_action.refresh_from_db()
            active_action.in_progress = False
            active_action.save()

    return "Erreur" in info, info