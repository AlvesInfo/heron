from apps.core.functions.functions_setups import settings
from django_celery_beat.models import PeriodicTask
from django_celery_results.models import TaskResult
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

one_hour_ago = timezone.localtime(timezone.now()) - timedelta(hours=1)
celery_tasks = TaskResult.objects.filter(
    task_name=task_name,
    status="STARTED",
    date_created__gte=one_hour_ago,
)


def celery_dashboard():
    context = {
        # Tâches périodiques (django-celery-beat)
        'periodic_tasks': PeriodicTask.objects.filter(enabled=True),

        # Tâches en cours (django-celery-results)
        'running_tasks': TaskResult.objects.filter(status='STARTED'),
        'pending_tasks': TaskResult.objects.filter(status='PENDING'),

        # Statistiques
        'stats': TaskResult.objects.values('status').annotate(
            count=Count('status')
        ),

        # Tâches récentes (dernière heure)
        'recent_tasks': TaskResult.objects.filter(
            date_created__gte=timezone.now() - timedelta(hours=1)
        ).order_by('-date_created')[:20],

    }
    print(context)


if __name__ == '__main__':
    celery_dashboard()

