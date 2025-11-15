
"""
Vues API pour le suivi de progression SSE
Endpoints pour récupérer l'état de jobs en cours

created at: 2025-01-10
created by: Paulo ALVES
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

from apps.core.models import SSEProgress


@login_required
@require_http_methods(["GET"])
def get_job_progress(request, job_id):
    """
    Récupère la progression d'un job spécifique

    URL: /api/core/sse-progress/<job_id>/
    Méthode: GET

    Returns:
        JSON avec les détails du job ou erreur 404
    """
    try:
        progress = SSEProgress.objects.get(
            job_id=job_id,
            user=request.user
        )
        return JsonResponse(progress.to_dict())
    except SSEProgress.DoesNotExist:
        return JsonResponse(
            {"error": f"Job {job_id} non trouvé"},
            status=404
        )


@login_required
@require_http_methods(["GET"])
def get_user_jobs(request):
    """
    Récupère tous les jobs de l'utilisateur connecté

    URL: /api/core/sse-progress/
    Méthode: GET

    Query params optionnels:
        - task_type: Filtrer par type de tâche
        - status: Filtrer par statut
        - limit: Limiter le nombre de résultats (défaut: 50)

    Returns:
        JSON avec la liste des jobs
    """
    queryset = SSEProgress.objects.filter(user=request.user)

    task_type = request.GET.get('task_type')
    if task_type:
        queryset = queryset.filter(task_type=task_type)

    status = request.GET.get('status')
    if status:
        queryset = queryset.filter(status=status)

    limit = int(request.GET.get('limit', 50))
    jobs = queryset[:limit]

    return JsonResponse({
        "count": jobs.count(),
        "jobs": [job.to_dict() for job in jobs]
    })


@login_required
@require_http_methods(["GET"])
def get_active_jobs(request):
    """
    Récupère uniquement les jobs actifs (pending ou in_progress)

    URL: /api/core/sse-progress/active/
    Méthode: GET

    Returns:
        JSON avec la liste des jobs actifs
    """
    jobs = SSEProgress.objects.filter(
        user=request.user,
        status__in=['pending', 'in_progress']
    ).order_by('-started_at')

    return JsonResponse({
        "count": jobs.count(),
        "jobs": [job.to_dict() for job in jobs]
    })


@login_required
@require_http_methods(["DELETE"])
def delete_job(request, job_id):
    """
    Supprime un job terminé ou échoué

    URL: /api/core/sse-progress/<job_id>/
    Méthode: DELETE

    Returns:
        JSON confirmation ou erreur
    """
    try:
        progress = SSEProgress.objects.get(
            job_id=job_id,
            user=request.user
        )

        if progress.status in ['pending', 'in_progress']:
            return JsonResponse(
                {"error": "Impossible de supprimer un job en cours"},
                status=400
            )

        progress.delete()
        return JsonResponse({
            "success": True,
            "message": f"Job {job_id} supprimé"
        })

    except SSEProgress.DoesNotExist:
        return JsonResponse(
            {"error": f"Job {job_id} non trouvé"},
            status=404
        )