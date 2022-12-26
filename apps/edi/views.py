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
    print(in_action)
    if request.method == "POST":
        """Si l'on envoie un POST alors on lance l'import"""
        if not in_action:
            start_edi_import.delay()
            in_action = True

    context = {
        "en_cours": in_action,
        "titre_table": (
            "INTEGRATION EN COURS DES FACTURES EN COURS, PATIENTEZ .... (Rafraîchissez la page)"
            if in_action else
            "Import des factures founisseurs EDI"
        )
    }
    print(context)
    return render(request, "edi/edi_import.html", context=context)
