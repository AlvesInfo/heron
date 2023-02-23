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
from django.shortcuts import render
from django.contrib import messages

from apps.parameters.bin.core import get_in_progress
from apps.edi.loops.imports_loop_pool import celery_import_launch, import_launch_bbgr
from apps.edi.loops.imports_loop_pool import (
    get_have_statment,
    get_have_monthly,
    get_have_retours,
    get_have_receptions,
    get_files_celery,
    get_retours_valid,
)


def import_edi_invoices(request):
    """Bouton d'import des factures edi"""

    request.session["level"] = 20
    in_action = get_in_progress()
    have_statment = get_have_statment()
    have_monthly = get_have_monthly()
    have_retours = get_have_retours()
    have_receptions = get_have_receptions()
    files_celery = get_files_celery()
    retours_valid = get_retours_valid()

    # Si l'on envoie un POST alors on lance l'import en tâche de fond celery
    if request.method == "POST":

        # On vérifie qu'il n'y a pas un import en cours
        if not in_action:
            bool_files = any(
                [have_statment, have_monthly, have_retours, have_receptions, files_celery]
            )

            # On vérifie qu'il y ait des fichiers
            if bool_files:
                user_pk = request.user.id

                if "bbgr_statment" in request.POST:
                    import_launch_bbgr("bbgr_statment", user_pk)
                elif "bbgr_monthly" in request.POST:
                    import_launch_bbgr("bbgr_monthly", user_pk)
                elif "bbgr_retours" in request.POST:
                    import_launch_bbgr("bbgr_retours", user_pk)
                elif "bbgr_receptions" in request.POST:
                    import_launch_bbgr("bbgr_receptions", user_pk)
                else:
                    celery_import_launch(user_pk)

                in_action = True

            else:
                request.session["level"] = 50
                messages.add_message(request, 50, "Il n'y a aucuns fichiers EDI à traiter !")

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
