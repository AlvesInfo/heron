# Guide d'intégration complet du système SSE de progression

## Vue d'ensemble

Ce guide explique comment installer et utiliser le système de progression SSE (Server-Sent Events) réutilisable dans l'application Heron.

**Avantages:**
- ✅ Temps réel instantané (pas de polling)
- ✅ Code DRY - réutilisable pour toutes les jauges
- ✅ Léger - juste `django-eventstream` à installer
- ✅ Compatible avec Gunicorn + UvicornWorker
- ✅ Persistance en base de données

**Composants créés:**
```
apps/core/
├── models/                           (package)
│   ├── __init__.py
│   ├── models.py
│   └── models_sse_progress.py        (modèle SSE)
├── views/                            (package)
│   ├── __init__.py
│   ├── views.py
│   └── views_sse_progress.py         (vues API SSE)
├── urls.py                           (URLs SSE intégrées)
├── bin/
│   └── sse_progress.py               (tracker SSE)
├── templates/core/
│   └── sse_progress_bar.html         (template)
└── AUTHOR_INFO.yaml

files/static/js/
└── sse_progress.js
```

---

## Étape 1: Installation de django-eventstream

### 1.1 Installer la bibliothèque

```bash
# Pour Django 3.2 (compatible Python 3.6+)
pip install django-eventstream==4.5.1
```

### 1.2 Ajouter à INSTALLED_APPS

Dans `heron/settings.py`:

```python
INSTALLED_APPS = [
    # ... vos apps existantes ...
    'django_eventstream',
]
```

### 1.3 Ajouter à MIDDLEWARE (important!)

Dans `heron/settings.py`, **après** `SessionMiddleware`:

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django_grip.GripMiddleware',  # ← Ajouter ici
    # ... reste du middleware ...
]
```

### 1.4 Configurer les URLs

Dans votre fichier `heron/urls.py` principal:

```python
from django.urls import path, include

urlpatterns = [
    # ... vos URLs existantes ...

    # Core URLs (contient API SSE Progress + endpoint events/)
    path(
        "core/",
        include(("apps.core.urls", "apps.core"), namespace="core"),
    ),
]
```

**Notes importantes:**
- Les URLs SSE (API + endpoint events/) sont maintenant **toutes dans `apps/core/urls.py`**.
- Plus besoin d'ajouter séparément l'URL `events/` dans heron/urls.py.
- **Toutes les URLs SSE sont préfixées par `/core/`** : `/core/events/`, `/core/sse-progress/`, etc.

---

## Étape 2: Vérifier le modèle SSEProgress

### 2.1 Le modèle est déjà créé

Le modèle `SSEProgress` est déjà dans: `apps/core/models/models_sse_progress.py`

Il est importé automatiquement via: `apps/core/models/__init__.py`

**Aucune action requise** - vous pouvez directement utiliser:
```python
from apps.core.models import SSEProgress
```

### 2.2 Créer et appliquer la migration

```bash
python manage.py makemigrations core
python manage.py migrate core
```

Vérifiez que la table est créée:

```bash
python manage.py dbshell
> .tables  # Vous devez voir core_sseprogress
```

---

## Étape 3: Exemple d'utilisation - Envoi d'emails

Voici un exemple complet d'utilisation du système SSE pour tracker l'envoi d'emails.

### 3.1 Créer la tâche Celery

`apps/invoices/tasks.py`:

```python
import uuid
from celery import shared_task
from apps.core.bin.sse_progress import SSEProgressTracker
from apps.core.models import SSEProgress

@shared_task(bind=True)
def send_invoices_with_sse(self, invoice_ids, user_id):
    """
    Envoie des factures avec suivi SSE
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # Générer un job_id unique
    job_id = str(uuid.uuid4())

    # Créer l'enregistrement en DB
    progress = SSEProgress.objects.create(
        job_id=job_id,
        user_id=user_id,
        task_type='email_sending',
        total_items=len(invoice_ids),
        status='pending'
    )

    # Créer le tracker SSE
    sse = SSEProgressTracker(job_id)

    try:
        # Marquer comme démarré
        progress.mark_as_started()
        sse.send_start(
            total=len(invoice_ids),
            message='Démarrage envoi des factures...'
        )

        # Traiter chaque facture
        for idx, invoice_id in enumerate(invoice_ids, 1):
            try:
                # Votre logique d'envoi d'email ici
                send_single_invoice(invoice_id)

                # Mettre à jour la progression
                progress.update_progress(processed=1, message=f"Facture {idx}/{len(invoice_ids)}")
                sse.send_progress(
                    current=idx,
                    total=len(invoice_ids),
                    message=f"Envoi facture {idx}/{len(invoice_ids)}"
                )

            except Exception as e:
                # En cas d'erreur sur un email
                progress.update_progress(processed=1, failed=1)
                sse.send_warning(f"Erreur sur facture {invoice_id}: {str(e)}")

        # Terminer avec succès
        progress.mark_as_completed()
        sse.send_complete(
            total=len(invoice_ids),
            message=f'✅ {progress.success_count} factures envoyées, {progress.failed_items} erreurs'
        )

    except Exception as e:
        # Erreur globale
        progress.mark_as_failed(str(e))
        sse.send_error(f"Erreur critique: {str(e)}")
        raise

    return {
        'job_id': job_id,
        'total': len(invoice_ids),
        'sent': progress.success_count,
        'failed': progress.failed_items
    }
```

### 3.2 Créer la vue Django

`apps/invoices/views.py`:

```python
import uuid
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from apps.invoices.tasks import send_invoices_with_sse
from apps.core.models import SSEProgress

@login_required
def send_invoices_page(request):
    """
    Page qui affiche la jauge de progression
    """
    if request.method == 'POST':
        # Récupérer les IDs de factures à envoyer
        invoice_ids = request.POST.getlist('invoice_ids')

        # Générer un job_id
        job_id = str(uuid.uuid4())

        # Créer l'enregistrement initial
        SSEProgress.objects.create(
            job_id=job_id,
            user=request.user,
            task_type='email_sending',
            total_items=len(invoice_ids),
            status='pending'
        )

        # Lancer la tâche Celery
        send_invoices_with_sse.delay(invoice_ids, request.user.id)

        return JsonResponse({
            'success': True,
            'job_id': job_id,
            'total': len(invoice_ids)
        })

    return render(request, 'invoices/send_invoices.html')
```

### 3.3 Créer le template

`apps/invoices/templates/invoices/send_invoices.html`:

```html
{% extends "base.html" %}
{% load static %}

{% block extra_css %}
<style>
    .invoice-form {
        max-width: 600px;
        margin: 50px auto;
        padding: 20px;
    }
</style>
{% endblock %}

{% block content %}
<div class="invoice-form">
    <h2>Envoi des factures par email</h2>

    <form id="sendForm" method="post">
        {% csrf_token %}

        <!-- Vos champs de formulaire ici -->
        <div class="form-group">
            <label>Factures à envoyer:</label>
            <input type="checkbox" name="invoice_ids" value="1"> Facture 1<br>
            <input type="checkbox" name="invoice_ids" value="2"> Facture 2<br>
            <input type="checkbox" name="invoice_ids" value="3"> Facture 3<br>
        </div>

        <button type="submit" class="btn btn-primary">
            📧 Envoyer les factures
        </button>
    </form>

    <!-- Zone où apparaîtra la jauge de progression -->
    <div id="progress-container"></div>
</div>
{% endblock %}

{% block extra_js %}
<!-- Charger le script SSE -->
<script src="{% static 'js/sse_progress.js' %}"></script>

<script>
document.getElementById('sendForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = new FormData(e.target);

    // Envoyer la requête
    const response = await fetch(window.location.href, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': formData.get('csrfmiddlewaretoken')
        }
    });

    const data = await response.json();

    if (data.success) {
        // Cacher le formulaire
        e.target.style.display = 'none';

        // Afficher la jauge de progression
        new SSEProgressUI('progress-container', data.job_id, {
            title: `Envoi de ${data.total} factures`,
            icon: '📧',
            showDetails: true,
            showStats: true,
            debug: true,  // Afficher les logs en console
            onComplete: (result) => {
                console.log('Envoi terminé!', result);
                // Vous pouvez rediriger ou afficher un message
                setTimeout(() => {
                    window.location.reload();
                }, 3000);
            },
            onError: (error) => {
                console.error('Erreur:', error);
                alert('Erreur: ' + error.error);
            }
        });
    }
});
</script>
{% endblock %}
```

---

## Étape 4: Utiliser le template réutilisable

Au lieu de créer l'UI en JavaScript, vous pouvez utiliser le template Django:

### 4.1 Template simplifié

`apps/invoices/templates/invoices/send_invoices_simple.html`:

```html
{% extends "base.html" %}
{% load static %}

{% block content %}
<div class="invoice-form">
    <h2>Envoi des factures</h2>

    <form id="sendForm" method="post">
        {% csrf_token %}
        <!-- Vos champs -->
        <button type="submit">📧 Envoyer</button>
    </form>

    <!-- Include du template réutilisable -->
    {% if job_id %}
        {% include 'core/sse_progress_bar.html' with job_id=job_id title='Envoi des factures' %}
    {% endif %}
</div>
{% endblock %}

{% block extra_js %}
<script src="{% static 'js/sse_progress.js' %}"></script>
<script>
// Votre code pour démarrer le processus
document.getElementById('sendForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);

    const response = await fetch(window.location.href, {
        method: 'POST',
        body: formData,
        headers: {'X-CSRFToken': formData.get('csrfmiddlewaretoken')}
    });

    const data = await response.json();

    if (data.success) {
        // Rediriger vers la même page avec job_id
        window.location.href = `?job_id=${data.job_id}`;
    }
});
</script>
{% endblock %}
```

---

## Étape 5: Autres cas d'usage

Le système SSE est réutilisable pour n'importe quelle tâche longue:

### 5.1 Import de fichiers EDI

```python
from apps.core.bin.sse_progress import SSEProgressTracker
from apps.core.models import SSEProgress

@shared_task
def import_edi_files(file_paths, user_id):
    job_id = str(uuid.uuid4())
    progress = SSEProgress.objects.create(
        job_id=job_id,
        user_id=user_id,
        task_type='edi_import',  # ← Différent type
        total_items=len(file_paths)
    )

    sse = SSEProgressTracker(job_id)
    progress.mark_as_started()
    sse.send_start(total=len(file_paths), message='Import EDI...')

    for idx, file_path in enumerate(file_paths, 1):
        import_single_file(file_path)
        progress.update_progress(processed=1)
        sse.send_progress(idx, len(file_paths), f"Fichier {idx}/{len(file_paths)}")

    progress.mark_as_completed()
    sse.send_complete(len(file_paths), "Import terminé")
```

### 5.2 Génération de rapports

```python
@shared_task
def generate_reports(report_ids, user_id):
    job_id = str(uuid.uuid4())
    progress = SSEProgress.objects.create(
        job_id=job_id,
        user_id=user_id,
        task_type='report_generation',  # ← Autre type
        total_items=len(report_ids),
        metadata={'format': 'PDF'}  # ← Métadonnées personnalisées
    )

    sse = SSEProgressTracker(job_id)
    progress.mark_as_started()
    sse.send_start(total=len(report_ids))

    for idx, report_id in enumerate(report_ids, 1):
        generate_pdf_report(report_id)
        progress.update_progress(processed=1)
        sse.send_progress(idx, len(report_ids))

    progress.mark_as_completed()
    sse.send_complete(len(report_ids))
```

---

## Étape 6: Configuration Gunicorn + UvicornWorker (production)

Pour que SSE fonctionne en production avec Gunicorn + UvicornWorker:

### 6.1 Lancer Gunicorn avec UvicornWorker et timeout adapté

```bash
gunicorn --access-logfile - \
    -k uvicorn.workers.UvicornWorker \
    --workers 9 \
    --timeout 1200 \
    --bind unix:/run/heron.sock \
    heron.asgi:application
```

**Important:** Le paramètre `--timeout 1200` (ou plus selon la durée de vos traitements) est **essentiel** pour maintenir les connexions SSE ouvertes pendant toute la durée du traitement.

### 6.2 Configuration selon la durée des traitements

- `--timeout 120`: Pour des traitements jusqu'à 2 minutes
- `--timeout 300`: Pour des traitements jusqu'à 5 minutes
- `--timeout 600`: Pour des traitements jusqu'à 10 minutes
- `--timeout 1200`: Pour des traitements jusqu'à 20 minutes

Ajustez selon la durée maximale de vos tâches.

### 6.3 Configuration systemd (recommandée)

Créez le fichier `/etc/systemd/system/heron.service`:

```ini
[Unit]
Description=Heron Django Application
After=network.target

[Service]
User=paulo
Group=www-data
WorkingDirectory=/home/paulo/heron
ExecStart=/home/paulo/.envs/heron/bin/gunicorn --access-logfile - \
    -k uvicorn.workers.UvicornWorker \
    --workers 9 \
    --timeout 1200 \
    --bind unix:/run/heron.sock \
    heron.asgi:application

[Install]
WantedBy=multi-user.target
```

Puis activez le service:
```bash
sudo systemctl enable heron
sudo systemctl start heron
sudo systemctl status heron
```

---

## Étape 7: Debug et troubleshooting

### 7.1 Activer le mode debug

Dans votre JavaScript:

```javascript
new SSEProgressUI('container', job_id, {
    debug: true  // ← Affiche tous les logs SSE en console
});
```

### 7.2 Vérifier que SSE fonctionne

Ouvrir la console du navigateur et vérifier:

```
[SSE] Connexion à /core/events/?channel=progress-abc-123
[SSE] ✅ Connecté
[SSE] 🚀 Start: {total: 500, status: 'started', ...}
[SSE] 📊 Progress: 5% {current: 25, total: 500, ...}
```

### 7.3 Erreurs courantes

**Erreur: "django_eventstream not found"**
→ `pip install django-eventstream`

**Erreur: "SSEProgressUI is not defined"**
→ Vérifier que `<script src="{% static 'js/sse_progress.js' %}"></script>` est chargé

**Pas de connexion SSE**
→ Vérifier que le middleware est dans `settings.py`

**Événements SSE ne s'affichent pas**
→ Vérifier que le `job_id` dans la tâche Celery correspond au `job_id` en frontend

---

## Résumé: Checklist d'installation

- [ ] `pip install django-eventstream==4.5.1`
- [ ] Ajouter `'django_eventstream'` à `INSTALLED_APPS`
- [ ] Ajouter `'django_grip.GripMiddleware'` dans `MIDDLEWARE`
- [ ] Le modèle `SSEProgress` est déjà dans `apps/core/models/models_sse_progress.py`
- [ ] `python manage.py makemigrations core && python manage.py migrate core`
- [ ] Ajouter dans `heron/urls.py`: `path("core/", include(("apps.core.urls", "apps.core"), namespace="core"))`
  - **Note:** Les URLs SSE (API + events/) sont toutes dans apps/core/urls.py
  - **Important:** Toutes les URLs SSE sont préfixées par `/core/`
- [ ] Utiliser `SSEProgressTracker` dans vos tâches Celery
- [ ] Charger `sse_progress.js` dans vos templates
- [ ] Créer instance `SSEProgressUI` en JavaScript

**Structure des fichiers (déjà créée):**
- ✅ `apps/core/models/models_sse_progress.py` (modèle SSEProgress)
- ✅ `apps/core/views/views_sse_progress.py` (vues API)
- ✅ `apps/core/urls.py` (URLs SSE intégrées)
- ✅ `apps/core/bin/sse_progress.py` (tracker SSE)
- ✅ `apps/core/templates/core/sse_progress_bar.html` (template)
- ✅ `files/static/js/sse_progress.js` (JavaScript)

---

## Support

Pour toute question sur l'implémentation, consulter:
- `apps/core/AUTHOR_INFO.yaml` pour les informations d'authorship
- Les exemples dans ce guide
- La documentation django-eventstream: https://github.com/fanout/django-eventstream