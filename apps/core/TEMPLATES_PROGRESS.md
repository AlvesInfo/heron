# Templates de code pour jauges de progression AJAX

Ce fichier contient des templates prêts à l'emploi pour implémenter rapidement une jauge de progression.

---

## Template complet - Vue + Tâche + Template

### 1. Vue Django

```python
# apps/[votre_app]/views/[votre_fichier].py
import uuid
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from apps.[votre_app].tasks import [votre_tache]

@login_required
def [nom_de_votre_vue](request):
    """
    Vue avec jauge de progression AJAX
    """
    if request.method == 'POST':
        # Générer un job_id unique
        job_id = str(uuid.uuid4())

        # Récupérer les données du formulaire
        # Exemple: items = request.POST.getlist('items')

        # Lancer la tâche Celery
        [votre_tache].delay(job_id, request.user.id)

        # Retourner le job_id au frontend
        return JsonResponse({
            'success': True,
            'job_id': job_id
        })

    # GET: Afficher la page
    context = {
        # Vos données de contexte
    }
    return render(request, '[votre_app]/[votre_template].html', context)
```

### 2. Tâche Celery

```python
# apps/[votre_app]/tasks.py
import time
from celery import shared_task
from apps.core.models import SSEProgress

@shared_task(name="[nom_de_votre_tache]")
def [votre_tache](job_id, user_id):
    """
    Tâche avec suivi de progression
    """
    # Créer l'entrée de progression
    progress = SSEProgress.objects.create(
        job_id=job_id,
        user_id=user_id,
        task_type='[type_de_tache]',  # Ex: 'import', 'email_sending', 'export'
        total_items=100,  # Nombre total d'items à traiter
        custom_title='Titre personnalisé de la jauge',  # OPTIONNEL: Titre personnalisé
        completion_message='Traitement terminé avec vos critères!'  # OPTIONNEL: Message final personnalisé
    )

    # Marquer comme démarré
    progress.mark_as_started()

    try:
        # Boucle de traitement
        for idx in range(1, 101):
            # --- VOTRE LOGIQUE DE TRAITEMENT ICI ---
            # traiter_item(idx)

            # Mettre à jour la progression
            progress.update_progress(
                processed=1,  # Nombre d'items traités dans cette itération
                message=f"Traitement de l'item {idx}/100"  # Message personnalisé
            )

            # Simulation d'un traitement
            time.sleep(0.1)

        # Marquer comme terminé
        progress.mark_as_completed()

        return {
            "status": "success",
            "job_id": job_id,
            "total": progress.total_items,
            "processed": progress.processed_items
        }

    except Exception as e:
        # En cas d'erreur
        progress.mark_as_failed(str(e))
        raise
```

### 3. Template HTML

```html
{% extends "heron/base_semantic.html" %}
{% load static %}

{% block menu_principal %}
    {% include "heron/menu_principal.html" %}
{% endblock menu_principal %}

{% block content %}

{% if user.is_authenticated %}

<div class="ui container" style="margin-top: 30px;">
    <div class="ui segment">
        <h2 class="ui header">
            <i class="[votre_icone] icon"></i>
            <div class="content">
                [Titre de votre page]
                <div class="sub header">[Description]</div>
            </div>
        </h2>

        <!-- Bouton de lancement -->
        <button id="btnLancer" class="ui primary button">
            <i class="play icon"></i>
            Lancer le traitement
        </button>

        <!-- Conteneur pour la jauge -->
        <div id="jauge" style="margin-top: 20px;"></div>
    </div>
</div>

{% else %}
    <p style="text-align: center;">Vous devez être connecté</p>
{% endif %}

{% endblock content %}

{% block script %}

<script src="{% static 'js/progress_polling.js' %}"></script>
<script>
$(document).ready(function() {
    $('#btnLancer').on('click', async function() {
        const btn = $(this);
        btn.addClass('loading disabled');

        try {
            // Envoyer la requête POST
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

                // Lancer la jauge de progression
                new ProgressPolling('jauge', data.job_id, {
                    title: '{{ progress_title|default:"[Titre de la jauge]" }}',  // Peut venir du contexte Django
                    icon: '[Emoji]',  // Ex: '📊', '📧', '📁'
                    showDetails: true,  // Affiche Total/Traités/Restants/Erreurs
                    showStats: true,    // Affiche les messages de progression
                    pollInterval: 500,
                    debug: true,
                    onComplete: (result) => {
                        console.log('✅ Traitement terminé!', result);
                        // result contient: failed_items, duration (arrondie), etc.
                        // Optionnel: recharger la page après 2s
                        setTimeout(() => {
                            btn.parent().show();
                            btn.removeClass('loading disabled');
                            // window.location.reload();
                        }, 2000);
                    },
                    onError: (error) => {
                        console.error('❌ Erreur:', error);
                        btn.removeClass('loading disabled');
                        btn.parent().show();
                    }
                });
            } else {
                alert('Erreur lors du lancement');
                btn.removeClass('loading disabled');
            }
        } catch (error) {
            console.error('Erreur:', error);
            alert('Erreur de communication avec le serveur');
            btn.removeClass('loading disabled');
        }
    });
});
</script>

{% endblock script %}
```

### 4. Configuration URLs

```python
# apps/[votre_app]/urls.py
from django.urls import path
from apps.[votre_app].views import [nom_de_votre_vue]

urlpatterns = [
    path('[votre-url]/', [nom_de_votre_vue], name='[nom_de_la_route]'),
]
```

---

## 📊 Fonctionnalités automatiques de la jauge

### Compteur d'erreurs automatique
La jauge affiche automatiquement une colonne "Erreurs" quand des items échouent:
- **Masqué par défaut** si aucune erreur
- **Apparaît automatiquement** dès qu'il y a des erreurs (rouge)
- Mis à jour en temps réel

Pour signaler une erreur dans votre tâche:
```python
progress.update_progress(
    processed=1,
    failed=1,  # ← Compteur d'erreurs
    message="Erreur sur l'item X",
)
```

### Durée arrondie
La durée est automatiquement arrondie à la seconde (sans virgules):
- `duration: 12.5678` → Affiché: `"13s"`
- Format final: `"Terminé avec succès ! (13s) - 2 erreurs"`

### Messages personnalisés depuis le backend

Vous pouvez définir des messages personnalisés lors de la création du job:

```python
progress = SSEProgress.objects.create(
    job_id=job_id,
    user_id=user_id,
    task_type="import",
    total_items=100,
    custom_title="Import de fichiers EDI",  # Titre de la jauge
    completion_message="Import terminé : 98 fichiers importés avec succès!",  # Message final
)
```

**Comportement:**
- `custom_title`: Peut être récupéré via l'API si nécessaire
- `completion_message`: Remplace le message par défaut à la fin du traitement
- Si `completion_message` n'est pas défini, le message par défaut est utilisé avec durée et erreurs

### Message par défaut (si completion_message non défini)
Format automatique:
- Sans erreurs: `"Terminé avec succès ! (12s)"`
- Avec erreurs: `"Terminé avec succès ! (12s) - 3 erreurs"`

---

## Snippets rapides

### Snippet 1: Tâche simple sans erreur

```python
@shared_task(name="ma_tache")
def ma_tache(job_id, user_id):
    progress = SSEProgress.objects.create(
        job_id=job_id, user_id=user_id, task_type="mon_type", total_items=100
    )
    progress.mark_as_started()

    for idx in range(1, 101):
        # Traitement
        progress.update_progress(processed=1)

    progress.mark_as_completed()
    return {"status": "success", "job_id": job_id}
```

### Snippet 2: Tâche avec gestion d'erreurs par item

```python
@shared_task(name="ma_tache")
def ma_tache(job_id, user_id, items):
    progress = SSEProgress.objects.create(
        job_id=job_id, user_id=user_id, task_type="mon_type", total_items=len(items)
    )
    progress.mark_as_started()

    for idx, item in enumerate(items, 1):
        try:
            # Traitement
            traiter_item(item)
            progress.update_progress(processed=1, message=f"Item {idx}/{len(items)} traité")
        except Exception as e:
            # Continuer malgré l'erreur
            progress.update_progress(processed=1, failed=1, message=f"Erreur item {idx}: {str(e)}")

    progress.mark_as_completed()
    return {"status": "success", "job_id": job_id}
```

### Snippet 3: JavaScript minimal

```javascript
new ProgressPolling('jauge', job_id, {
    title: 'Mon traitement',
    icon: '📊',
    onComplete: (result) => console.log('Terminé!', result)
});
```

### Snippet 4: JavaScript avec toutes les options

```javascript
new ProgressPolling('jauge', job_id, {
    pollInterval: 500,
    title: 'Mon processus',
    icon: '📊',
    showDetails: true,
    showStats: true,
    autoHideOnComplete: false,
    autoHideDelay: 3000,
    debug: true,
    onStart: (data) => {
        console.log('Démarrage:', data);
    },
    onProgress: (data) => {
        console.log('Progression:', data.progress_percentage + '%');
    },
    onComplete: (data) => {
        console.log('Terminé!', data);
        // window.location.reload();
    },
    onError: (error) => {
        console.error('Erreur:', error);
        alert('Une erreur est survenue');
    }
});
```

---

## Cas d'usage spécifiques

### Cas 1: Import de fichiers

```python
# Vue
@login_required
def import_fichiers(request):
    if request.method == "POST":
        job_id = str(uuid.uuid4())
        fichiers = request.FILES.getlist("fichiers")

        # Sauvegarder les fichiers temporairement
        fichier_paths = []
        for f in fichiers:
            path = handle_uploaded_file(f)
            fichier_paths.append(path)

        task_import_fichiers.delay(job_id, request.user.id, fichier_paths)
        return JsonResponse({"success": True, "job_id": job_id})

    return render(request, "import_fichiers.html")


# Tâche
@shared_task(name="import_fichiers")
def task_import_fichiers(job_id, user_id, fichier_paths):
    progress = SSEProgress.objects.create(
        job_id=job_id, user_id=user_id, task_type="file_import", total_items=len(fichier_paths)
    )
    progress.mark_as_started()

    for idx, path in enumerate(fichier_paths, 1):
        importer_fichier(path)
        progress.update_progress(processed=1, message=f"Fichier {idx}/{len(fichier_paths)} importé")

    progress.mark_as_completed()
    return {"status": "success", "job_id": job_id}
```

### Cas 2: Envoi d'emails en masse

```python
# Tâche
@shared_task(name="envoi_emails")
def task_envoi_emails(job_id, user_id, destinataires):
    progress = SSEProgress.objects.create(
        job_id=job_id, user_id=user_id, task_type="email_sending", total_items=len(destinataires)
    )
    progress.mark_as_started()

    for idx, dest in enumerate(destinataires, 1):
        try:
            envoyer_email(dest)
            progress.update_progress(
                processed=1, message=f"Email {idx}/{len(destinataires)} envoyé à {dest['email']}"
            )
        except Exception as e:
            progress.update_progress(
                processed=1, failed=1, message=f"Erreur email {dest['email']}: {str(e)}"
            )

    progress.mark_as_completed()
    return {
        "status": "success",
        "job_id": job_id,
        "sent": progress.success_count,
        "failed": progress.failed_items,
    }
```

### Cas 3: Export de données

```python
# Vue
@login_required
def export_donnees(request):
    if request.method == "POST":
        job_id = str(uuid.uuid4())
        date_debut = request.POST.get("date_debut")
        date_fin = request.POST.get("date_fin")

        task_export.delay(job_id, request.user.id, date_debut, date_fin)
        return JsonResponse({"success": True, "job_id": job_id})

    return render(request, "export_donnees.html")


# Tâche
@shared_task(name="export_donnees")
def task_export(job_id, user_id, date_debut, date_fin):
    # Récupérer les données
    donnees = recuperer_donnees(date_debut, date_fin)

    progress = SSEProgress.objects.create(
        job_id=job_id, user_id=user_id, task_type="data_export", total_items=len(donnees)
    )
    progress.mark_as_started()

    # Créer le fichier Excel
    wb = openpyxl.Workbook()
    ws = wb.active

    for idx, ligne in enumerate(donnees, 1):
        ecrire_ligne_excel(ws, idx, ligne)
        progress.update_progress(processed=1, message=f"Ligne {idx}/{len(donnees)} exportée")

    # Sauvegarder
    fichier_path = f"/tmp/export_{job_id}.xlsx"
    wb.save(fichier_path)

    progress.mark_as_completed()
    progress.metadata = {"fichier_path": fichier_path}
    progress.save()

    return {"status": "success", "job_id": job_id, "fichier": fichier_path}
```

---

## Checklist d'implémentation

Lors de l'implémentation d'une nouvelle jauge:

- [ ] Créer la vue Django qui retourne `job_id`
- [ ] Créer la tâche Celery avec `SSEProgress`
- [ ] Créer le template HTML avec le conteneur `<div id="jauge"></div>`
- [ ] Charger le script `progress_polling.js`
- [ ] Initialiser `new ProgressPolling()` dans le JavaScript
- [ ] Ajouter l'URL dans `urls.py`
- [ ] Tester avec `debug: true` dans les options JavaScript

---

## Debugging

### Activer les logs

```javascript
new ProgressPolling('jauge', job_id, {
    debug: true  // Affiche tous les appels polling en console
});
```

### Vérifier l'API manuellement

```bash
# Vérifier qu'un job existe
curl http://localhost:8000/core/sse-progress/[job_id]/

# Lister tous les jobs actifs
curl http://localhost:8000/core/sse-progress/active/
```

### Logs Python

```python
# Dans votre tâche
import logging

logger = logging.getLogger(__name__)


@shared_task(name="ma_tache")
def ma_tache(job_id, user_id):
    logger.info(f"Démarrage du job {job_id}")
    # ...
    logger.info(f"Job {job_id} terminé")
```

---

## Icônes courantes

| Type de tâche | Icône Emoji | Icône Semantic UI |
|---------------|-------------|-------------------|
| Import | 📁 | `folder open icon` |
| Export | 📤 | `upload icon` |
| Email | 📧 | `mail icon` |
| Génération PDF | 📄 | `file pdf icon` |
| Calcul | 🧮 | `calculator icon` |
| Traitement | ⚙️ | `cog icon` |
| Synchronisation | 🔄 | `sync icon` |
| Validation | ✅ | `check circle icon` |
| Progression | 📊 | `chart line icon` |

---

## Exemple complet fonctionnel

Voir l'implémentation de référence:
- Template: `apps/edi/templates/edi/edi_jauge_import.html`
- Vue: `apps/edi/views/views_jauges.py`
- Tâche: `apps/edi/tasks.py` - fonction `task_test_import_jauge`
- JavaScript: `/files/static/js/progress_polling.js`
