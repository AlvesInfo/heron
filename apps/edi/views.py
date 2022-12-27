from django.shortcuts import render

from apps.parameters.models import ActionInProgress
from apps.edi.tasks import start_edi_import


def import_edi_invoices(request):
    """Bouton d'import des factrues edi"""

    try:
        in_action_object = ActionInProgress.objects.get(action="import_edi_invoices")
        in_action = in_action_object.in_progress
    except ActionInProgress.DoesNotExist:
        in_action = False

    if request.method == "POST":
        """Si l'on envoie un POST alors on lance l'import en tâche de fond celery"""
        if not in_action:
            start_edi_import.delay()
            in_action = True

    context = {
        "en_cours": in_action,
        "titre_table": (
            "INTEGRATION EN COURS, PATIENTEZ... (Revenez plus tard)"
            if in_action else
            "Import des factures founisseurs EDI"
        )
    }

    return render(request, "edi/edi_import.html", context=context)
