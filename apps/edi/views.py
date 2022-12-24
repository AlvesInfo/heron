from django.shortcuts import render

from apps.parameters.models import ActionInProgress
from apps.edi.loops.imports_loop_pool import main as main_import_loop


def import_edi_invoices(request):
    """Bouton d'import des factrues edi"""

    if request.method == "POST":
        """Si l'on envoie un POST alors on lance l'import"""
        main_import_loop()

    try:
        in_action_object = ActionInProgress.objects.get(action="import_edi_invoices")
        in_action = in_action_object.in_progress
    except ActionInProgress.DoesNotExist:
        in_action = False

    context = {
        "en_cours": in_action,
        "titre_table": (
            "INTEGRATION EN COURS DES FACTURES EN COURS, PATIENTEZ .... (Rafraîchissez la page)"
            if in_action else
            "Import des factures founisseurs EDI"
        )
    }

    return render(request, "edi/edi_import.html", context=context)
