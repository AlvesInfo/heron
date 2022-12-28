# pylint: disable=E0401,E1101
"""
FR : Module core des parametrages
EN : Core module parameters

Commentaire:

created at: 2022-12-27
created by: Paulo ALVES

modified at: 2022-12-27
modified by: Paulo ALVES
"""
from django_celery_results.models import TaskResult

from apps.parameters.models import ActionInProgress


def get_in_progress():
    """Renvoi si un process d'intégration edi est en cours"""
    try:
        in_action_object = ActionInProgress.objects.get(action="import_edi_invoices")
        in_action = in_action_object.in_progress

        # On contrôle si une tâche est réellement en cours pour éviter les faux positifs
        if in_action:
            celery_tasks = TaskResult.objects.filter(
                task_name="apps.edi.tasks.start_edi_import"
            ).exclude(status__in=["SUCCESS", "FAILURE"])
            in_action = celery_tasks.exists()

    except ActionInProgress.DoesNotExist:
        in_action = False

    return in_action
