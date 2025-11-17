"""Utilitaires pour gérer et surveiller les tâches Celery"""
from typing import Dict, List, Tuple
from heron.celery import app


def get_celery_tasks_status() -> Dict:
    """
    Récupère le statut de toutes les tâches Celery

    Returns:
        dict: {
            'has_tasks': bool,
            'total': int,
            'active': int,
            'scheduled': int,
            'reserved': int,
            'workers': list,
            'details': dict
        }
    """
    inspect = app.control.inspect()

    active = inspect.active() or {}
    scheduled = inspect.scheduled() or {}
    reserved = inspect.reserved() or {}

    total_active = sum(len(tasks) for tasks in active.values() if tasks)
    total_scheduled = sum(len(tasks) for tasks in scheduled.values() if tasks)
    total_reserved = sum(len(tasks) for tasks in reserved.values() if tasks)
    total = total_active + total_scheduled + total_reserved

    # Liste des workers actifs
    workers = list(set(
        list(active.keys()) + list(scheduled.keys()) + list(reserved.keys())
    ))

    return {
        'has_tasks': total > 0,
        'total': total,
        'active': total_active,
        'scheduled': total_scheduled,
        'reserved': total_reserved,
        'workers': workers,
        'details': {
            'active': active,
            'scheduled': scheduled,
            'reserved': reserved
        }
    }


def has_active_celery_tasks() -> bool:
    """
    Vérifie s'il y a des tâches Celery en cours

    Returns:
        bool: True si des tâches sont en cours, False sinon
    """
    status = get_celery_tasks_status()
    return status['has_tasks']


def get_active_tasks_list() -> List[Dict]:
    """
    Récupère la liste détaillée de toutes les tâches actives

    Returns:
        list: Liste des tâches avec leurs détails
    """
    inspect = app.control.inspect()
    active = inspect.active() or {}

    tasks_list = []
    for worker, tasks in active.items():
        if tasks:
            for task in tasks:
                tasks_list.append({
                    'worker': worker,
                    'task_id': task.get('id'),
                    'task_name': task.get('name'),
                    'args': task.get('args'),
                    'kwargs': task.get('kwargs'),
                    'time_start': task.get('time_start'),
                })

    return tasks_list


def wait_for_celery_idle(timeout: int = 300, check_interval: int = 2) -> Tuple[bool, int]:
    """
    Attend que toutes les tâches Celery soient terminées

    Args:
        timeout: Temps maximum d'attente en secondes
        check_interval: Intervalle entre les vérifications en secondes

    Returns:
        tuple: (success: bool, remaining_tasks: int)
    """
    import time

    inspect = app.control.inspect()
    elapsed = 0

    while elapsed < timeout:
        active = inspect.active() or {}
        scheduled = inspect.scheduled() or {}
        reserved = inspect.reserved() or {}

        total = sum(
            len(tasks) for task_dict in [active, scheduled, reserved]
            for tasks in task_dict.values() if tasks
        )

        if total == 0:
            return True, 0

        time.sleep(check_interval)
        elapsed += check_interval

    # Timeout atteint
    status = get_celery_tasks_status()
    return False, status['total']


def get_celery_workers_stats() -> Dict:
    """
    Récupère les statistiques des workers Celery

    Returns:
        dict: Statistiques des workers
    """
    inspect = app.control.inspect()
    stats = inspect.stats() or {}

    workers_info = {}
    for worker, data in stats.items():
        workers_info[worker] = {
            'pool': data.get('pool', {}).get('implementation'),
            'max_concurrency': data.get('pool', {}).get('max-concurrency'),
            'total_tasks': data.get('total', {}),
        }

    return workers_info


def is_celery_available() -> bool:
    """
    Vérifie si au moins un worker Celery est disponible

    Returns:
        bool: True si au moins un worker est actif
    """
    inspect = app.control.inspect()
    stats = inspect.stats()
    return stats is not None and len(stats) > 0