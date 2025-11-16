# pylint: disable=
"""
FR : Module des vues pour les imports
EN : Views module for imports

Commentaire:

created at: 2022-12-26
created by: Paulo ALVES

modified at: 2022-12-26
modified by: Paulo ALVES
"""

import uuid
import threading
from django.shortcuts import render
from django.contrib import messages
from django.http import JsonResponse

from apps.parameters.bin.core import get_in_progress
from apps.core.models import SSEProgress
from apps.edi.loops.imports_loop_pool import celery_import_launch, import_launch_bbgr
from apps.edi.loops.imports_loop_pool import (
    get_have_statment,
    get_have_monthly,
    get_have_retours,
    get_have_receptions,
    get_files_celery,
    get_retours_valid,
)
from apps.invoices.bin.pre_controls import control_insertion


def import_edi_invoices(request):
    """Bouton d'import des factures edi"""
    request.session["level"] = 20

    # On contrôle qu'il n'y ait pas des factures non finalisées, mais envoyées par mail
    not_finalize = control_insertion()

    if not_finalize:
        request.session["level"] = 50
        messages.add_message(
            request,
            50,
            (
                "Vous ne pouvez pas importer, car la facturation est déjà envoyée par mail, "
                "mais non finalisée"
            ),
        )
        context = {
            "margin_table": 50,
            "titre_table": "Import des factures founisseurs EDI",
            "not_finalize": True,
        }
        return render(request, "edi/edi_import.html", context=context)

    in_action = get_in_progress()
    have_statment = get_have_statment()
    have_monthly = get_have_monthly()
    have_retours = get_have_retours()
    have_receptions = get_have_receptions()
    files_celery = get_files_celery()
    retours_valid = get_retours_valid()

    # Si l'on envoie un POST alors on lance l'import en tâche de fond celery
    if request.method == "POST" and not in_action:
        bool_files = any(
            [have_statment, have_monthly, have_retours, have_receptions, files_celery]
        )

        # On vérifie qu'il y ait des fichiers
        if bool_files:
            user_pk = request.user.id
            job_id = str(uuid.uuid4())  # Générer un job_id unique

            # Créer le SSEProgress AVANT de lancer les tâches
            if "bbgr_statment" in request.POST:
                progress = SSEProgress.objects.create(
                    job_id=job_id,
                    user_id=user_pk,
                    task_type="bbgr_import",
                    total_items=1,
                    custom_title="Import BBGR Statment",
                    metadata={"success": [], "failed": []},
                )
                progress.mark_as_started()
                # Lancer dans un thread séparé
                thread = threading.Thread(
                    target=import_launch_bbgr,
                    args=("bbgr_statment", user_pk, job_id),
                    daemon=True,
                )
                thread.start()
            elif "bbgr_monthly" in request.POST:
                progress = SSEProgress.objects.create(
                    job_id=job_id,
                    user_id=user_pk,
                    task_type="bbgr_import",
                    total_items=1,
                    custom_title="Import BBGR Monthly",
                    metadata={"success": [], "failed": []},
                )
                progress.mark_as_started()
                thread = threading.Thread(
                    target=import_launch_bbgr,
                    args=("bbgr_monthly", user_pk, job_id),
                    daemon=True,
                )
                thread.start()
            elif "bbgr_retours" in request.POST:
                progress = SSEProgress.objects.create(
                    job_id=job_id,
                    user_id=user_pk,
                    task_type="bbgr_import",
                    total_items=1,
                    custom_title="Import BBGR Retours",
                    metadata={"success": [], "failed": []},
                )
                progress.mark_as_started()
                thread = threading.Thread(
                    target=import_launch_bbgr,
                    args=("bbgr_retours", user_pk, job_id),
                    daemon=True,
                )
                thread.start()
            elif "bbgr_receptions" in request.POST:
                progress = SSEProgress.objects.create(
                    job_id=job_id,
                    user_id=user_pk,
                    task_type="bbgr_import",
                    total_items=1,
                    custom_title="Import BBGR Receptions",
                    metadata={"success": [], "failed": []},
                )
                progress.mark_as_started()
                thread = threading.Thread(
                    target=import_launch_bbgr,
                    args=("bbgr_receptions", user_pk, job_id),
                    daemon=True,
                )
                thread.start()
            else:
                # Pour les imports EDI normaux, compter le nombre de fichiers
                total_files = len(files_celery)
                progress = SSEProgress.objects.create(
                    job_id=job_id,
                    user_id=user_pk,
                    task_type="edi_import",
                    total_items=total_files,
                    custom_title="Import des factures EDI",
                    metadata={"success": [], "failed": []},
                )
                progress.mark_as_started()
                # Lancer dans un thread séparé
                thread = threading.Thread(
                    target=celery_import_launch, args=(user_pk, job_id), daemon=True
                )
                thread.start()

            # Retourner JSON immédiatement
            return JsonResponse({"success": True, "job_id": job_id})

        else:
            return JsonResponse(
                {"success": False, "error": "Il n'y a aucuns fichiers EDI à traiter !"}
            )

    context = {
        "en_cours": in_action,
        "margin_table": 50,
        "titre_table": (
            "INTEGRATION EN COURS, PATIENTEZ..."
            if in_action
            else "Import des factures founisseurs EDI"
        ),
        "have_statment": have_statment,
        "have_monthly": have_monthly,
        "have_retours": have_retours,
        "have_receptions": have_receptions,
        "files_celery": files_celery,
        "retours_valid": retours_valid,
    }

    return render(request, "edi/edi_import.html", context=context)
