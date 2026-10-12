# Système de progression AJAX - apps/core

## Vue d'ensemble

Ce dossier contient un système **générique et réutilisable** de suivi de progression en temps réel via polling AJAX.

Utilisable pour:
- ✅ Envoi d'emails en masse
- ✅ Import de fichiers EDI
- ✅ Génération de rapports
- ✅ Exports de données
- ✅ Traitements batch
- ✅ **N'importe quelle tâche longue**

**Avantages:**
- ✅ Aucune dépendance externe (pas de django-eventstream, Pushpin, etc.)
- ✅ Fonctionne avec Django standard (pas besoin d'ASGI)
- ✅ Compatible avec tous les navigateurs
- ✅ Simple et fiable
- ✅ Utilise Semantic UI pour l'interface

**🚀 Quick Start:**
- **Pour générer du code rapidement:** Voir `TEMPLATES_PROGRESS.md` (templates prêts à l'emploi)
- **Pour comprendre le système:** Continuer la lecture de ce README

---

## Structure des fichiers

```
apps/core/
├── models/                           (package)
│   ├── __init__.py                   imports automatiques
│   ├── models.py                     modèles existants
│   └── models_sse_progress.py        ✅ Modèle SSEProgress (nom conservé pour compatibilité)
├── views/                            (package)
│   ├── __init__.py                   imports automatiques
│   ├── views.py                      vues existantes
│   └── views_sse_progress.py         ✅ Vues API REST pour polling
├── urls.py                           ✅ URLs API intégrées
├── README_PROGRESS.md                ✅ Ce fichier - Documentation
├── TEMPLATES_PROGRESS.md             ⭐ Templates de code prêts à l'emploi
└── AUTHOR_INFO.yaml

files/static/js/
└── progress_polling.js               ✅ JavaScript pour polling AJAX
```

### 🐍 Python Backend

| Fichier | Description | Statut |
|---------|-------------|--------|
| `models/models_sse_progress.py` | Modèle `SSEProgress` (importé automatiquement) | ✅ Prêt |
| `views/views_sse_progress.py` | API REST pour récupérer l'état des jobs | ✅ Prêt |
| `urls.py` | Routes API REST | ✅ Prêt |

### 🌐 JavaScript Frontend

| Fichier | Description | Statut |
|---------|-------------|--------|
| `/files/static/js/progress_polling.js` | Classe `ProgressPolling` avec Semantic UI | ✅ Prêt |

---

## Installation

**Aucune dépendance externe nécessaire!**

```bash
# 1. Le modèle SSEProgress est déjà dans models/models_sse_progress.py
# Il est importé automatiquement via models/__init__.py

# 2. Migrer (si ce n'est pas déjà fait)
python manage.py makemigrations core
python manage.py migrate core

# 3. Configurer URLs dans heron/urls.py (déjà fait)
# path("core/", include(("apps.core.urls", "apps.core"), namespace="core"))
# Important: Toutes les URLs API sont préfixées par /core/
```

C'est tout! Aucune configuration supplémentaire nécessaire.

---

## Utilisation

### Côté Python (Vue Django)

```python
import uuid
from django.http import JsonResponse
from apps.core.models import SSEProgress


def ma_vue(request):
    if request.method == "POST":
        # Générer un job_id unique
        job_id = str(uuid.uuid4())

        # Lancer la tâche Celery
        ma_tache_celery.delay(job_id, request.user.id)

        # Retourner le job_id au frontend
        return JsonResponse({"success": True, "job_id": job_id})

    return render(request, "mon_template.html")
```

### Côté Python (Tâche Celery)

```python
import time
from celery import shared_task
from apps.core.models import SSEProgress


@shared_task(name="ma_tache")
def ma_tache_celery(job_id, user_id):
    # Créer l'entrée de progression
    progress = SSEProgress.objects.create(
        job_id=job_id, user_id=user_id, task_type="mon_type", total_items=100
    )

    # Marquer comme démarré
    progress.mark_as_started()

    # Traiter les items
    for idx in range(1, 101):
        # Faire le traitement
        traiter_item(idx)

        # Mettre à jour la progression
        progress.update_progress(processed=1)

        time.sleep(0.1)  # Simulation

    # Marquer comme terminé
    progress.mark_as_completed()

    return {"status": "success", "job_id": job_id}
```

### Côté HTML (Template)

```html
{% load static %}

<!-- Conteneur pour la jauge -->
<div id="jauge"></div>

<!-- Charger le script -->
<script src="{% static 'js/progress_polling.js' %}"></script>

<script>
$(document).ready(function() {
    $('#btnLancer').on('click', async function() {
        const btn = $(this);
        btn.addClass('loading disabled');

        try {
            // Appeler la vue pour lancer la tâche
            const response = await fetch(window.location.href, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': '{{ csrf_token }}'
                }
            });

            const data = await response.json();

            if (data.success) {
                // Cacher le bouton
                btn.parent().hide();

                // Lancer le polling
                new ProgressPolling('jauge', data.job_id, {
                    title: 'Mon traitement',
                    icon: '📊',
                    showDetails: true,
                    showStats: true,
                    pollInterval: 500,  // Polling toutes les 500ms
                    debug: true,
                    onComplete: (result) => {
                        console.log('✅ Terminé!', result);
                        // Réafficher le bouton après 2s
                        setTimeout(() => {
                            btn.parent().show();
                            btn.removeClass('loading disabled');
                        }, 2000);
                    },
                    onError: (error) => {
                        console.error('❌ Erreur:', error);
                        btn.removeClass('loading disabled');
                        btn.parent().show();
                    }
                });
            }
        } catch (error) {
            console.error('Erreur:', error);
            btn.removeClass('loading disabled');
        }
    });
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
- `current_message`: Message de progression actuel
- `metadata`: JSON libre pour données custom

### 2. Polling AJAX (ProgressPolling)

Le JavaScript interroge l'API REST toutes les 500ms:
- Envoie une requête GET à `/core/sse-progress/<job_id>/`
- Reçoit l'état actuel du job en JSON
- Met à jour l'interface Semantic UI
- Continue jusqu'à ce que le job soit terminé

### 3. Frontend (Semantic UI)

Affiche la jauge avec composants Semantic UI:
- Progress bar animée avec pourcentage
- Labels colorés selon le statut (bleu=en cours, vert=terminé, rouge=erreur)
- Statistiques (total, traités, restants)
- Messages de statut
- Gestion automatique des erreurs de connexion

---

## Options de configuration

```javascript
new ProgressPolling('containerId', 'job-id', {
    pollInterval: 500,           // Intervalle de polling en ms (défaut: 500)
    title: 'Mon processus',      // Titre affiché
    icon: '📊',                  // Icône
    showDetails: true,           // Afficher les statistiques détaillées
    showStats: true,             // Afficher les messages de statut
    autoHideOnComplete: false,   // Masquer automatiquement à la fin
    autoHideDelay: 3000,         // Délai avant masquage (si autoHide=true)
    debug: false,                // Logs console pour debug

    // Callbacks
    onStart: (data) => {},       // Appelé au démarrage
    onProgress: (data) => {},    // Appelé à chaque mise à jour
    onComplete: (data) => {},    // Appelé à la fin
    onError: (error) => {}       // Appelé en cas d'erreur
});
```

---

## API Endpoints

Définis dans `apps/core/urls.py`:

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/core/sse-progress/` | GET | Liste tous les jobs de l'utilisateur |
| `/core/sse-progress/active/` | GET | Liste jobs actifs uniquement |
| `/core/sse-progress/<job_id>/` | GET | Détails d'un job (utilisé par le polling) |
| `/core/sse-progress/<job_id>/delete/` | DELETE | Supprimer un job terminé |

**Format de réponse pour `/core/sse-progress/<job_id>/`:**

```json
{
    "job_id": "abc-123",
    "status": "in_progress",
    "task_type": "mon_type",
    "total_items": 100,
    "processed_items": 45,
    "failed_items": 0,
    "progress_percentage": 45,
    "current_message": "Traitement en cours...",
    "started_at": "2025-01-16T10:30:00Z",
    "completed_at": null,
    "duration": 22.5
}
```

---

## Exemples de tâches supportées

### 1. Envoi d'emails

```python
task_type = "email_sending"
metadata = {"campaign_id": 123}
```

### 2. Import EDI

```python
task_type = "edi_import"
metadata = {"file_format": "ORDERS", "supplier_id": 456}
```

### 3. Génération rapports

```python
task_type = "report_generation"
metadata = {"report_type": "monthly", "format": "PDF"}
```

### 4. Export comptabilité

```python
task_type = "accounting_export"
metadata = {"destination": "X3", "period": "2025-01"}
```

---

## Comparaison: Polling vs SSE

| Critère | Polling AJAX | SSE |
|---------|--------------|-----|
| Requêtes | 1 toutes les 500ms | 1 connexion permanente |
| Latence | 0-500ms | Instantané |
| Charge serveur | Faible | Faible |
| Installation | Aucune | django-eventstream + Pushpin/ASGI |
| Complexité | Très simple | Moyenne à élevée |
| Compatibilité | 100% navigateurs | 95% navigateurs |
| Configuration serveur | Standard (WSGI) | Nécessite ASGI |
| Fiabilité | ✅ Excellente | ⚠️ Dépend de la config |

**Le polling AJAX a été choisi pour:**
- ✅ Aucune dépendance externe
- ✅ Configuration serveur standard
- ✅ Grande simplicité
- ✅ Fiabilité maximale
- ✅ 500ms de latence est acceptable pour des tâches longues

---

## Production

Le système de polling AJAX fonctionne avec **n'importe quelle configuration serveur**:

```bash
# Gunicorn standard (WSGI)
gunicorn --access-logfile - \
    --workers 9 \
    --bind unix:/run/heron.sock \
    heron.wsgi:application
```

Aucune configuration spéciale nécessaire! Le polling fonctionne avec WSGI standard.

---

## Debug

### Activer les logs JavaScript

```javascript
new ProgressPolling('container', 'job-id', {
    debug: true  // ← Affiche tous les appels polling en console
});
```

Console navigateur:
```
[Polling] Démarrage du polling pour job abc-123
[Polling] Données reçues: {status: 'in_progress', progress_percentage: 45, ...}
[Polling] Arrêt du polling
```

### Vérifier l'API manuellement

```bash
# Obtenir le statut d'un job
curl http://localhost:8000/core/sse-progress/abc-123/

# Lister tous les jobs actifs
curl http://localhost:8000/core/sse-progress/active/
```

---

## Support et questions

**Exemple concret:**
- Template: `apps/edi/templates/edi/edi_jauge_import.html`
- View: `apps/edi/views/views_jauges.py`
- Task: `apps/edi/tasks.py` - fonction `task_test_import_jauge`

**Documentation:**
- `README_PROGRESS.md` - Ce fichier
- `AUTHOR_INFO.yaml` - Informations d'authorship

**JavaScript:**
- Fichier: `/files/static/js/progress_polling.js`
- Utilise Semantic UI Progress, Labels, Statistics, Messages