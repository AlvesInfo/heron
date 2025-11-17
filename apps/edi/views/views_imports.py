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
from asgiref.sync import async_to_sync

from django.shortcuts import render, redirect, reverse
from django.contrib import messages
from django.http import JsonResponse

from apps.parameters.bin.core import get_in_progress
from apps.core.models import SSEProgress
from apps.edi.loops.imports_loop_pool import (
    celery_import_launch,
    import_launch_bbgr,
    get_all_import_checks_async,
)
from apps.invoices.bin.pre_controls import control_insertion


def import_edi_invoices(request):
    """Bouton d'import des factures edi"""
    request.session["level"] = 20

    in_action = get_in_progress()

    if in_action:
        request.session["level"] = 50
        messages.add_message(
            request,
            50,
            "Vous ne pouvez pas importer, imports en cours ...",
        )
        return redirect(reverse("home"))

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

    # Récupération parallèle et asynchrone de toutes les vérifications
    (
        have_statment,
        have_monthly,
        have_retours,
        have_receptions,
        files_celery,
        retours_valid,
    ) = async_to_sync(get_all_import_checks_async)()

    # Si l'on envoie un POST alors on lance l'import en tâche de fond celery
    if request.method == "POST" and not in_action:
        bool_files = any(
            [have_statment, have_monthly, have_retours, have_receptions, files_celery]
        )

        # On vérifie qu'il y ait des fichiers
        if bool_files:
            user_pk = request.user.id
            job_id = str(uuid.uuid4())  # Générer un job_id unique
            print(request.POST)
            # Créer le SSEProgress AVANT de lancer les tâches
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

            progress = SSEProgress.objects.create(
                job_id=job_id,
                user_id=user_pk,
                total_items=total_files,
                task_type=task_type,
                custom_title=custom_title,
                metadata={"success": [], "failed": []},
            )
            progress.mark_as_started()

            # Lancement d'un thread séparé
            thread = threading.Thread(
                target=target,
                args=args,
                daemon=True,
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
