""""
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
import time
import logging
import sys
import os
from asgiref.sync import async_to_sync

from django.shortcuts import render
from django.contrib import messages
from django.http import JsonResponse

from apps.core.models import SSEProgress
from apps.edi.loops.imports_loop_pool import (
    celery_import_launch,
    import_launch_bbgr,
    get_all_import_checks_async,
    get_import_controls_async,
)

IMPORT_TEMPLATE = "edi/edi_import.html"

# Configuration du logger pour afficher dans la console sans duplication
logger = logging.getLogger(__name__)
if os.environ.get('RUN_MAIN') == 'true':
    # Processus principal : configurer le logger pour afficher
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(filename)s:%(lineno)d [%(funcName)s] - %(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
else:
    # Processus reloader : désactiver complètement les logs
    logger.setLevel(logging.CRITICAL + 1)
    logger.propagate = False


def import_edi_invoices(request):
    """Bouton d'import des factures edi"""
    start_total = time.perf_counter()

    request.session["level"] = 20

    # Exécution parallèle de get_in_progress et control_insertion
    start = time.perf_counter()
    in_action, not_finalize = async_to_sync(get_import_controls_async)()
    time_controls = time.perf_counter() - start
    logger.info(f"[IMPORT_EDI_INVOICES] get_import_controls_async: {time_controls:.4f}s")

    context = {
            "en_cours": False,
            "margin_table": 50,
            "titre_table": "Import des factures founisseurs EDI",
            "submit_url": "edi:import_edi_invoices",
        }

    if in_action:
        context.update({"en_cours": True, "titre_table": "INTEGRATION EN COURS, PATIENTEZ..."})
        time_total = time.perf_counter() - start_total
        logger.info(f"[IMPORT_EDI_INVOICES] TOTAL (in_action): {time_total:.4f}s")
        return render(request, IMPORT_TEMPLATE, context=context)

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
        context.update({"not_finalize": True})

        time_total = time.perf_counter() - start_total
        logger.info(f"[IMPORT_EDI_INVOICES] TOTAL (not_finalize): {time_total:.4f}s")
        return render(request, IMPORT_TEMPLATE, context=context)

    # Récupération parallèle et asynchrone de toutes les vérifications
    start = time.perf_counter()
    (
        have_statment,
        have_monthly,
        have_retours,
        have_receptions,
        files_celery,
        retours_valid,
    ) = async_to_sync(get_all_import_checks_async)()
    time_async_checks = time.perf_counter() - start
    logger.info(f"[IMPORT_EDI_INVOICES] get_all_import_checks_async: {time_async_checks:.4f}s")

    # Si l'on envoie un POST alors, on lance l'import en tâche de fond celery
    if request.method == "POST" and not in_action:
        start = time.perf_counter()
        bool_files = any(
            [have_statment, have_monthly, have_retours, have_receptions, files_celery]
        )
        time_check_files = time.perf_counter() - start
        logger.info(f"[IMPORT_EDI_INVOICES] check_files: {time_check_files:.4f}s")

        # On vérifie qu'il y ait des fichiers
        if bool_files:
            user_pk = request.user.id
            job_id = str(uuid.uuid4())  # Générer un job_id unique
            logger.info(request.POST)
            # Créer le SSEProgress AVANT de lancer les tâches
            start = time.perf_counter()
            if "bbgr_statment" in request.POST:
                # Pour les statment bbgr 1 pour import et 2 pour validation
                total_files = 2
                task_type = "bbgr_import"
                custom_title = "Import BBGR Statment"
                target = import_launch_bbgr
                args = ("bbgr_statment", user_pk, job_id)

            elif "bbgr_monthly" in request.POST:
                # Pour les monthly bbgr 1 pour import et 2 pour validation
                total_files = 2
                task_type = "bbgr_import"
                custom_title = "Import BBGR Monthly"
                target = import_launch_bbgr
                args = ("bbgr_monthly", user_pk, job_id)

            elif "bbgr_retours" in request.POST:
                # Pour les retours bbgr 1 pour import et 2 pour validation
                total_files = 2
                task_type = "bbgr_import"
                custom_title = "Import BBGR Retours"
                target = import_launch_bbgr
                args = ("bbgr_retours", user_pk, job_id)

            elif "bbgr_receptions" in request.POST:
                # Pour les receptions bbgr 1 pour import et 2 pour validation
                total_files = 2
                task_type = "bbgr_import"
                custom_title = "Import BBGR Receptions"
                target = import_launch_bbgr
                args = ("bbgr_receptions", user_pk, job_id)

            else:
                # Pour les imports EDI normaux, compter le nombre de fichiers
                total_files = len(files_celery) + 1
                task_type = "edi_import"
                custom_title = "Import des factures EDI"
                target = celery_import_launch
                args = (user_pk, job_id)

            time_determine_type = time.perf_counter() - start
            logger.info(f"[IMPORT_EDI_INVOICES] determine_import_type: {time_determine_type:.4f}s")

            start = time.perf_counter()
            progress = SSEProgress.objects.create(
                job_id=job_id,
                user_id=user_pk,
                total_items=total_files,
                task_type=task_type,
                custom_title=custom_title,
                metadata={"success": [], "failed": []},
            )
            progress.mark_as_started()
            time_create_progress = time.perf_counter() - start
            logger.info(f"[IMPORT_EDI_INVOICES] create_SSEProgress: {time_create_progress:.4f}s")

            # Lancement d'un thread séparé
            start = time.perf_counter()
            thread = threading.Thread(
                target=target,
                args=args,
                daemon=True,
            )
            thread.start()
            time_thread_start = time.perf_counter() - start
            logger.info(f"[IMPORT_EDI_INVOICES] thread_start: {time_thread_start:.4f}s")

            time_total = time.perf_counter() - start_total
            logger.info(f"[IMPORT_EDI_INVOICES] TOTAL (success): {time_total:.4f}s")

            # Retourner JSON immédiatement
            return JsonResponse({"success": True, "job_id": job_id})

        else:
            time_total = time.perf_counter() - start_total
            logger.info(f"[IMPORT_EDI_INVOICES] TOTAL (no_files): {time_total:.4f}s")
            return JsonResponse(
                {"success": False, "error": "Il n'y a aucuns fichiers EDI à traiter !"}
            )

    start = time.perf_counter()
    context.update({
        "have_statment": have_statment,
        "have_monthly": have_monthly,
        "have_retours": have_retours,
        "have_receptions": have_receptions,
        "files_celery": files_celery,
        "retours_valid": retours_valid,
    })
    time_context_update = time.perf_counter() - start
    logger.info(f"[IMPORT_EDI_INVOICES] context_update: {time_context_update:.4f}s")

    start = time.perf_counter()
    response = render(request, IMPORT_TEMPLATE, context=context)
    time_render = time.perf_counter() - start
    logger.info(f"[IMPORT_EDI_INVOICES] render: {time_render:.4f}s")

    time_total = time.perf_counter() - start_total
    logger.info(f"[IMPORT_EDI_INVOICES] TOTAL (GET): {time_total:.4f}s")
    return response
