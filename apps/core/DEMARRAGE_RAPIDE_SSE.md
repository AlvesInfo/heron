# Démarrage rapide - Système SSE de progression

## Installation en 5 minutes

### 1. Installer la bibliothèque

```bash
# Pour Django 3.2 (compatible Python 3.6+)
pip install django-eventstream==4.5.1
```

### 2. Configuration Django (heron/settings.py)

Ajouter à `INSTALLED_APPS`:
```python
INSTALLED_APPS = [
    # ... autres apps ...
    'django_eventstream',
]
```

Ajouter à `MIDDLEWARE` (après SessionMiddleware):
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django_grip.GripMiddleware',  # ← AJOUTER ICI
    # ... reste ...
]
```

### 3. URLs (heron/urls.py)

```python
from django.urls import path, include

urlpatterns = [
    # ... vos URLs ...

    # Core URLs (contient API SSE Progress + endpoint events/)
    path(
        "core/",
        include(("apps.core.urls", "apps.core"), namespace="core"),
    ),
]
```

**Note:**
- L'URL `events/` est maintenant dans `apps/core/urls.py`, pas besoin de l'ajouter séparément.
- Toutes les URLs SSE sont préfixées par `/core/` : `/core/events/`, `/core/sse-progress/`, etc.

### 4. Ajouter le modèle

**Le modèle est déjà créé:** `apps/core/models/models_sse_progress.py`

**Il est importé automatiquement** via `apps/core/models/__init__.py`

**Aucune action requise** - le modèle est déjà accessible via `from apps.core.models import SSEProgress`

### 5. Migration

```bash
python manage.py makemigrations core
python manage.py migrate core
```

---

## Utilisation - Exemple minimal

### Dans votre tâche Celery:

```python
import uuid
from celery import shared_task
from apps.core.bin.sse_progress import SSEProgressTracker
from apps.core.models import SSEProgress

@shared_task
def ma_tache_longue(items, user_id):
    job_id = str(uuid.uuid4())

    # Créer en DB
    progress = SSEProgress.objects.create(
        job_id=job_id,
        user_id=user_id,
        task_type='mon_type',
        total_items=len(items)
    )

    # Tracker SSE
    sse = SSEProgressTracker(job_id)

    # Démarrer
    progress.mark_as_started()
    sse.send_start(total=len(items))

    # Traiter
    for idx, item in enumerate(items, 1):
        process_item(item)
        progress.update_progress(processed=1)
        sse.send_progress(idx, len(items))

    # Terminer
    progress.mark_as_completed()
    sse.send_complete(len(items))

    return job_id
```

### Dans votre template:

```html
{% load static %}

<div id="progress-container"></div>

<script src="{% static 'js/sse_progress.js' %}"></script>
<script>
// Après avoir lancé la tâche et reçu le job_id:
new SSEProgressUI('progress-container', job_id, {
    title: 'Mon processus',
    debug: true
});
</script>
```

---

## C'est tout!

Votre système de progression en temps réel est prêt.

**Prochaines étapes:**
- Consulter `GUIDE_INTEGRATION_SSE.md` pour des exemples détaillés
- Voir les exemples dans `apps/invoices/bin/api_gmail/` pour l'envoi d'emails

**Debug:**
Ajouter `debug: true` dans les options JavaScript pour voir les logs SSE en console.