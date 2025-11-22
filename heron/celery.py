import os

from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")

port = settings.REDIS_PORT if settings.BASE_DIR.name == "heron" else 6740

BROKER_URL = f"redis://:heron@{settings.REDIS_HOST}:{port}/0"

app = Celery("heron", broker=BROKER_URL)

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")
app.conf.update(
    worker_max_tasks_per_child=100,
    worker_max_memory_per_child=512000,  # 500MB
    worker_disable_rate_limits=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Load task modules from all registered Django apps.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
