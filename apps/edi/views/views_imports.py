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
from apps.edi.tasks import start_edi_import
from apps.edi.loops.imports_loop_pool import celery_import_launch
from apps.edi.loops.imports_loop_pool import have_files


def import_edi_invoices(request):
    """Bouton d'import des factures edi"""

    request.session["level"] = 20
    in_action = get_in_progress()

    # Si l'on envoie un POST alors on lance l'import en tâche de fond celery
    if request.method == "POST":

        # On vérifie qu'il n'y a pas un import en cours
        if not in_action:
            bool_files = have_files()

            # On vérifie qu'il y ai des fichiers
            if bool_files:
                # start_edi_import.delay()
                celery_import_launch()
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
    }

    return render(request, "edi/edi_import.html", context=context)
