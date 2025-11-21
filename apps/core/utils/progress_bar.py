"""
FR: Module utilitaire pour les progress bar

Commentaire:

created at: 2025-11-119
created by: Paulo ALVES

modified at: 2025-11-119
modified by: Paulo ALVES
"""

from apps.core.models import SSEProgress
from apps.core.functions.functions_setups import transaction


def update_progress_threaded(job_id: str, **kwargs):
    """Met à jour le SSEProgress avec un commit immédiat dans une transaction séparée"""
    with transaction.atomic():
        progress = SSEProgress.objects.select_for_update().get(job_id=job_id)
        try:
            if "mark_as_failed" in kwargs:
                progress.mark_as_failed("Une erreur c'est produite, consulter les logs")

            elif "mark_as_completed" in kwargs:
                progress.mark_as_completed()

            else:
                progress.update_progress(**kwargs)
        except TypeError:
            print("kwargs : ", kwargs)
            print("kwargs : ", "mmark_as_failed" in kwargs)
            print("mark_as_completed" in kwargs)
            breakpoint()