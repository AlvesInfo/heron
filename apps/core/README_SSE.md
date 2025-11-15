# Système SSE de progression - apps/core

## Vue d'ensemble

Ce dossier contient un système **générique et réutilisable** de suivi de progression en temps réel via Server-Sent Events (SSE).

Utilisable pour:
- ✅ Envoi d'emails en masse
- ✅ Import de fichiers EDI
- ✅ Génération de rapports
- ✅ Exports de données
- ✅ Traitements batch
- ✅ **N'importe quelle tâche longue**

---

## Structure des fichiers

```
apps/core/
├── models/                           (package)
│   ├── __init__.py                   imports automatiques
│   ├── models.py                     modèles existants
│   └── models_sse_progress.py        ✅ Modèle SSEProgress
├── views/                            (package)
│   ├── __init__.py                   imports automatiques
│   ├── views.py                      vues existantes
│   └── views_sse_progress.py         ✅ Vues API SSE
├── urls.py                           ✅ URLs SSE intégrées
├── bin/
│   └── sse_progress.py               ✅ Tracker SSE
├── templates/core/
│   └── sse_progress_bar.html         ✅ Template réutilisable
└── docs/
    ├── DEMARRAGE_RAPIDE_SSE.md
    ├── GUIDE_INTEGRATION_SSE.md
    ├── README_SSE.md
    └── AUTHOR_INFO.yaml

files/static/js/
└── sse_progress.js                   ✅ JavaScript SSE
```

### 🐍 Python Backend

| Fichier | Description | Statut |
|---------|-------------|--------|
| `models/models_sse_progress.py` | Modèle `SSEProgress` (importé automatiquement) | ✅ Prêt |
| `bin/sse_progress.py` | Classe `SSEProgressTracker` pour envoyer événements SSE | ✅ Prêt |
| `views/views_sse_progress.py` | API REST pour récupérer l'état des jobs | ✅ Prêt |
| `urls.py` | Routes SSE + endpoint events/ (lignes 45-57) | ✅ Prêt |

### 📄 Templates

| Fichier | Description | Statut |
|---------|-------------|--------|
| `templates/core/sse_progress_bar.html` | Template réutilisable avec jauge | ✅ Prêt |

### 🌐 JavaScript Frontend

| Fichier | Description | Statut |
|---------|-------------|--------|
| `/files/static/js/sse_progress.js` | Classes `SSEProgressListener` et `SSEProgressUI` | ✅ Prêt |

### 📚 Documentation

| Fichier | Description |
|---------|-------------|
| `DEMARRAGE_RAPIDE_SSE.md` | Installation en 5 minutes |
| `GUIDE_INTEGRATION_SSE.md` | Guide complet avec exemples |
| `README_SSE.md` | Ce fichier |
| `AUTHOR_INFO.yaml` | Informations d'authorship |

---

## Installation

Voir le fichier `DEMARRAGE_RAPIDE_SSE.md` pour l'installation complète.

**Résumé rapide:**
```bash
# 1. Installer (versions compatibles Django 3.2)
pip install django-eventstream==4.5.1

# 2. Configurer settings.py
# - Ajouter 'django_eventstream' à INSTALLED_APPS
# - Ajouter 'django_grip.GripMiddleware' à MIDDLEWARE

# 3. Le modèle SSEProgress est déjà dans models/models_sse_progress.py
# Il est importé automatiquement via models/__init__.py

# 4. Migrer
python manage.py makemigrations core
python manage.py migrate core

# 5. Configurer URLs dans heron/urls.py
# path("core/", include(("apps.core.urls", "apps.core"), namespace="core"))
# Note: Les URLs SSE (API + events/) sont toutes dans apps/core/urls.py
# Important: Toutes les URLs SSE sont préfixées par /core/
```

---

## Utilisation

### Côté Python (Celery task)

```python
from apps.core.bin.sse_progress import SSEProgressTracker
from apps.core.models import SSEProgress

@shared_task
def ma_tache(items, user_id):
    job_id = str(uuid.uuid4())
    progress = SSEProgress.objects.create(
        job_id=job_id,
        user_id=user_id,
        task_type='mon_type',
        total_items=len(items)
    )

    sse = SSEProgressTracker(job_id)
    progress.mark_as_started()
    sse.send_start(total=len(items))

    for idx, item in enumerate(items, 1):
        traiter_item(item)
        progress.update_progress(processed=1)
        sse.send_progress(idx, len(items))

    progress.mark_as_completed()
    sse.send_complete(len(items))
```

### Côté JavaScript (Frontend)

```html
<div id="gauge"></div>

<script src="{% static 'js/sse_progress.js' %}"></script>
<script>
new SSEProgressUI('gauge', job_id, {
    title: 'Mon processus',
    onComplete: () => console.log('Fini!')
});
</script>
```

---

## Architecture

### 1. Base de données (SSEProgress model)

Stocke l'état de chaque job:
- `job_id`: Identifiant unique (UUID)
- `user`: Utilisateur qui a lancé
- `task_type`: Type de tâche (email_sending, import, etc.)
- `status`: pending, in_progress, completed, failed
- `total_items`, `processed_items`, `failed_items`
- `metadata`: JSON libre pour données custom

### 2. SSE Events (SSEProgressTracker)

Envoie des événements temps réel:
- **start**: Début du processus
- **progress**: Mise à jour (current, total, percentage)
- **complete**: Fin avec succès
- **error**: Erreur fatale
- **warning**: Erreur non-bloquante

### 3. Frontend (SSEProgressUI)

Affiche la jauge:
- Barre de progression animée
- Pourcentage
- Détails (total, traités, restants)
- Messages de statut
- Reconnexion automatique

---

## API Endpoints

Définis dans `apps/core/urls.py` (lignes 45-48):

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/core/sse-progress/` | GET | Liste tous les jobs de l'utilisateur |
| `/core/sse-progress/active/` | GET | Liste jobs actifs uniquement |
| `/core/sse-progress/<job_id>/` | GET | Détails d'un job |
| `/core/sse-progress/<job_id>/delete/` | DELETE | Supprimer un job terminé |

---

## Exemples de tâches supportées

### 1. Envoi d'emails

```python
task_type='email_sending'
metadata={'campaign_id': 123}
```

### 2. Import EDI

```python
task_type='edi_import'
metadata={'file_format': 'ORDERS', 'supplier_id': 456}
```

### 3. Génération rapports

```python
task_type='report_generation'
metadata={'report_type': 'monthly', 'format': 'PDF'}
```

### 4. Export comptabilité

```python
task_type='accounting_export'
metadata={'destination': 'X3', 'period': '2025-01'}
```

---

## Différences avec Polling HTTP

| Critère | Polling HTTP | SSE (ce système) |
|---------|--------------|------------------|
| Requêtes | 1/seconde = 180 req/3min | 1 connexion |
| Latence | 0-1 seconde | Instantané |
| Charge serveur | Moyenne | Faible |
| Réutilisabilité | Code dupliqué | Classe générique |
| Installation | Rien | django-eventstream |
| Complexité | Simple | Moyenne |

---

## Différences avec Django Channels (WebSocket)

| Critère | SSE | Channels |
|---------|-----|----------|
| Installation | `pip install django-eventstream` | Channels + Redis + Daphne |
| Configuration | ~10 lignes | ~50 lignes |
| Serveur | Gunicorn + UvicornWorker (ASGI) | Daphne (ASGI) |
| Communication | Serveur → Client | Bidirectionnelle |
| Pour ce cas | ✅ Parfait | ❌ Overkill |

**SSE est recommandé pour votre use case car:**
- ✅ Communication unidirectionnelle suffisante (serveur → client)
- ✅ Beaucoup plus simple que Channels
- ✅ Compatible avec votre stack Gunicorn + UvicornWorker existante
- ✅ Suffisant pour 3-10 jauges différentes

---

## Production (Gunicorn + UvicornWorker)

SSE nécessite Gunicorn avec UvicornWorker et un timeout adapté pour les connexions longues:

```bash
gunicorn --access-logfile - \
    -k uvicorn.workers.UvicornWorker \
    --workers 9 \
    --timeout 120 \
    --bind unix:/run/heron.sock \
    heron.asgi:application
```

**Important:** Le paramètre `--timeout 1200` (ou plus selon la durée de vos traitements) est **essentiel** pour maintenir les connexions SSE ouvertes pendant toute la durée du traitement.

**Configuration typique:**
- `--timeout 120`: Pour des traitements jusqu'à 2 minutes
- `--timeout 300`: Pour des traitements jusqu'à 5 minutes
- `--timeout 1200`: Pour des traitements jusqu'à 20 minutes
- Ajustez selon la durée maximale de vos tâches

---

## Debug

### Activer les logs JavaScript

```javascript
new SSEProgressUI('container', job_id, {
    debug: true  // ← Affiche tous les événements SSE en console
});
```

### Logs Python

Les logs SSE utilisent `LOGGER_INVOICES` (configuré dans `heron/loggers.py`).

### Vérifier la connexion SSE

Console navigateur:
```
[SSE] Connexion à /core/events/?channel=progress-abc-123
[SSE] ✅ Connecté
[SSE] 🚀 Start: {total: 500, ...}
```

---

## Support et questions

**Documentation:**
- `DEMARRAGE_RAPIDE_SSE.md` - Installation rapide
- `GUIDE_INTEGRATION_SSE.md` - Guide complet avec exemples détaillés
- `AUTHOR_INFO.yaml` - Informations d'authorship

**Exemples concrets:**
- Envoi emails: `apps/invoices/bin/api_gmail/tasks_gmail_with_progress.py`
- Template: `apps/core/templates/core/sse_progress_bar.html`

**Bibliothèque:**
- django-eventstream docs: https://github.com/fanout/django-eventstream