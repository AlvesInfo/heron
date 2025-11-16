# pylint: disable=
"""
FR : Module des vues pour les jauges des imports
EN : Views module for imports gauges

Commentaire:

created at: 2025-11-16
created by: Paulo ALVES

modified at: 2025-11-16
modified by: Paulo ALVES
"""

import uuid

from django.shortcuts import render
from django.http import JsonResponse

from apps.edi.tasks import task_test_import_jauge


def import_jauge(request):
    """Vue de la jauge des imports"""

    if request.method == "POST":
        # Générer le job_id
        job_id = str(uuid.uuid4())

        # Lancer la tâche Celery en arrière-plan
        task_test_import_jauge.delay(job_id, request.user.id)

        # Retourner immédiatement avec le job_id
        return JsonResponse(
            {
                "success": True,
                "job_id": job_id,
            }
        )

    # GET : Afficher la page avec le formulaire
    context = {}
    return render(request, "edi/edi_jauge_import.html", context)
