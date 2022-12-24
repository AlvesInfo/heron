from django.shortcuts import render
from django_q.tasks import async_task

from apps.parameters.models import ActionInProgress
from apps.edi.loops.imports_loop_pool import main as edi_main


def import_edi_invoices(request):
    """Bouton d'import des factrues edi"""

    try:
        in_action_object = ActionInProgress.objects.get(action="import_edi_invoices")
        in_action = in_action_object.in_progress
    except ActionInProgress.DoesNotExist:
        in_action = False

    if request.method == "POST":
        """Si l'on envoie un POST alors on lance l'import"""
        if not in_action:
            async_task(edi_main)
            in_action = True

    context = {
        "en_cours": in_action,
        "titre_table": (
            "INTEGRATION EN COURS DES FACTURES EN COURS, PATIENTEZ .... (Rafraîchissez la page)"
            if in_action else
            "Import des factures founisseurs EDI"
        )
    }

    return render(request, "edi/edi_import.html", context=context)
