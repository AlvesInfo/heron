""" "
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

from django.shortcuts import render
from django.http import JsonResponse

from apps.core.models import SSEProgress
from apps.parameters.bin.core import (
    have_action_in_progress,
    have_send_email_without_finalize,
    set_message,
)
from apps.edi.loops.imports_loop_pool import (
    celery_import_launch,
    import_launch_bbgr,
    get_all_import_checks_async,
)

IMPORT_TEMPLATE = "edi/edi_import.html"


def import_edi_invoices(request):
    """Bouton d'import des factures edi"""

    context = {
        "en_cours": False,
        "margin_table": 50,
        "titre_table": "Import des factures founisseurs EDI",
        "submit_url": "edi:import_edi_invoices",
    }

    in_action = have_action_in_progress()

    if in_action:
        set_message(
            request, 50, "Il y a des intégrations en cours, réessayez plus tard !"
        )

        return render(request, IMPORT_TEMPLATE, context=context)

    not_finalize = have_send_email_without_finalize()

    if not_finalize:
        message = (
            "Vous ne pouvez pas Importer des factures EDI, "
            "car la facturation est déjà envoyée par mail, mais non finalisée"
        )
        set_message(request, 50, message)
        context.update(
            {
                "not_finalize": True,
            }
        )

        return render(request, IMPORT_TEMPLATE, context=context)

    # Récupération parallèle et asynchrone de toutes les vérifications
    (
        have_statment,
        have_monthly,
        have_retours,
        have_receptions,
        files_celery,
        retours_valid,
    ) = async_to_sync(get_all_import_checks_async)()

    # Si l'on envoie un POST alors, on lance l'import en tâche de fond celery
    if request.method == "POST":
        bool_files = any(
            [have_statment, have_monthly, have_retours, have_receptions, files_celery]
        )

        # On vérifie qu'il y ait des fichiers
        if bool_files:
            user_pk = request.user.id
            job_id = str(uuid.uuid4())  # Générer un job_id unique

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
            set_message(request, 50, "Il n'y a aucuns fichiers EDI à traiter !")

            return JsonResponse(
                {"success": False, "error": "Il n'y a aucuns fichiers EDI à traiter !"}
            )

    context.update(
        {
            "have_statment": have_statment,
            "have_monthly": have_monthly,
            "have_retours": have_retours,
            "have_receptions": have_receptions,
            "files_celery": files_celery,
            "retours_valid": retours_valid,
        }
    )

    return render(request, IMPORT_TEMPLATE, context=context)
