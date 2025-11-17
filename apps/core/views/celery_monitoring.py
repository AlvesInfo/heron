"""Vues pour le monitoring des tâches Celery"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required

from apps.core.utils.celery_utils import (
    get_celery_tasks_status,
    has_active_celery_tasks,
    get_active_tasks_list,
    get_celery_workers_stats,
    is_celery_available
)


@staff_member_required
@require_http_methods(["GET"])
def celery_status(request):
    """
    Retourne le statut complet des tâches Celery
    Usage: GET /celery/status/
    """
    status = get_celery_tasks_status()
    return JsonResponse(status)


@staff_member_required
@require_http_methods(["GET"])
def celery_check_idle(request):
    """
    Vérifie s'il y a des tâches en cours
    Usage: GET /celery/check-idle/
    Returns: {'is_idle': bool, 'tasks_count': int}
    """
    has_tasks = has_active_celery_tasks()
    status = get_celery_tasks_status()

    return JsonResponse({
        'is_idle': not has_tasks,
        'has_tasks': has_tasks,
        'tasks_count': status['total']
    })


@staff_member_required
@require_http_methods(["GET"])
def celery_active_tasks(request):
    """
    Liste toutes les tâches actives
    Usage: GET /celery/active-tasks/
    """
    tasks = get_active_tasks_list()
    return JsonResponse({
        'count': len(tasks),
        'tasks': tasks
    })


@staff_member_required
@require_http_methods(["GET"])
def celery_workers(request):
    """
    Informations sur les workers Celery
    Usage: GET /celery/workers/
    """
    if not is_celery_available():
        return JsonResponse({
            'available': False,
            'error': 'Aucun worker Celery disponible'
        }, status=503)

    workers = get_celery_workers_stats()
    return JsonResponse({
        'available': True,
        'workers': workers,
        'count': len(workers)
    })