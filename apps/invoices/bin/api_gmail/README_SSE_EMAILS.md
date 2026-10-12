# ⚠️ Ce fichier est obsolète

## Le système SSE a été remplacé par un système de polling AJAX

**Documentation principale:** Voir `apps/core/README_PROGRESS.md`

---

## Envoi d'emails avec suivi de progression

Le système d'envoi d'emails par batch utilise désormais le **système de polling AJAX** au lieu de SSE.

### Pourquoi ce changement?

Le système SSE nécessitait:
- ❌ django-eventstream (dépendance externe)
- ❌ Configuration complexe (middleware, ASGI, etc.)
- ❌ Compatibilité limitée avec Django 3.2

Le nouveau système de polling AJAX offre:
- ✅ Aucune dépendance externe
- ✅ Configuration minimale
- ✅ Interface Semantic UI cohérente
- ✅ Simplicité et fiabilité maximales

---

## Architecture actuelle

### Backend

- **Tâche Celery**: Utilise le modèle `SSEProgress` (nom conservé pour compatibilité)
  - Met à jour la progression via `progress.update_progress(processed=1)`
  - Plus besoin de `SSEProgressTracker` ou `sse.send_*()`

- **Vues Django**: Retournent un `job_id` au frontend
  - Le frontend lance le polling AJAX automatiquement

- **API REST**: Endpoints existants dans `apps/core/urls.py`
  - `/core/sse-progress/<job_id>/` - Utilisé par le polling

### Frontend

- **JavaScript**: `files/static/js/progress_polling.js`
  - Classe `ProgressPolling` (remplace `SSEProgressUI`)
  - Polling toutes les 500ms
  - Interface Semantic UI

- **Composants UI**:
  - Barre de progression Semantic UI
  - Labels colorés (bleu=en cours, vert=succès, rouge=erreur)
  - Statistiques en temps réel
  - Messages de progression

---

## Utilisation recommandée

### 1. Dans votre tâche Celery

```python
import uuid
from celery import shared_task
from apps.core.models import SSEProgress


@shared_task(name="envoi_emails")
def envoi_emails_task(job_id, user_id, invoices):
    # Créer l'entrée de progression
    progress = SSEProgress.objects.create(
        job_id=job_id, user_id=user_id, task_type="email_sending", total_items=len(invoices)
    )

    # Marquer comme démarré
    progress.mark_as_started()

    # Traiter chaque email
    for idx, invoice in enumerate(invoices, 1):
        try:
            send_email(invoice)
            # Mettre à jour avec message personnalisé
            progress.update_progress(
                processed=1, message=f"Email {idx}/{len(invoices)} envoyé : {invoice.reference}"
            )
        except Exception as e:
            # En cas d'erreur
            progress.update_progress(
                processed=1, failed=1, message=f"Erreur email {invoice.reference}: {str(e)}"
            )

    # Marquer comme terminé
    progress.mark_as_completed()

    return {"status": "success", "job_id": job_id}
```

### 2. Dans votre vue Django

```python
import uuid
from django.http import JsonResponse


def send_invoices_view(request):
    if request.method == "POST":
        # Générer un job_id unique
        job_id = str(uuid.uuid4())

        # Récupérer les factures à envoyer
        invoices = get_invoices_to_send(request)

        # Lancer la tâche Celery
        envoi_emails_task.delay(job_id, request.user.id, invoices)

        # Retourner le job_id
        return JsonResponse({"success": True, "job_id": job_id})

    return render(request, "invoices/send_invoices.html")
```

### 3. Dans votre template

```html
{% load static %}

<div id="jauge"></div>

<script src="{% static 'js/progress_polling.js' %}"></script>
<script>
$(document).ready(function() {
    $('#btnEnvoyer').on('click', async function() {
        const btn = $(this);
        btn.addClass('loading disabled');

        try {
            const response = await fetch(window.location.href, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': '{{ csrf_token }}'
                }
            });

            const data = await response.json();

            if (data.success) {
                btn.parent().hide();

                // Lancer le polling avec détails personnalisés
                new ProgressPolling('jauge', data.job_id, {
                    title: 'Envoi des factures par email',
                    icon: '📧',
                    showDetails: true,
                    showStats: true,
                    pollInterval: 500,
                    debug: true,
                    onComplete: (result) => {
                        console.log('✅ Envoi terminé!', result);
                        setTimeout(() => {
                            window.location.reload();
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

## Fonctionnalités

### ✅ Suivi en temps réel (500ms de latence)
- Polling AJAX toutes les 500ms
- Affichage fluide de la progression
- Latence acceptable pour l'envoi d'emails

### ✅ Affichage détaillé avec Semantic UI
- Barre de progression animée
- Pourcentage en temps réel
- Statistiques: total, traités, restants
- Messages personnalisés pour chaque email
- Labels colorés selon le statut

### ✅ Gestion des erreurs
- Continue l'envoi en cas d'erreur sur un email
- Compteur d'erreurs séparé
- Messages d'erreur affichés
- Trace en base de données

### ✅ Persistance
- État sauvegardé en base de données (modèle SSEProgress)
- Récupération possible après rafraîchissement
- Historique des envois

---

## Exemple de flux

1. **L'utilisateur clique sur "Envoyer les factures"**
   - Requête POST vers la vue Django
   - Génération d'un `job_id` unique
   - Lancement de la tâche Celery
   - Retour du `job_id` au frontend

2. **Le frontend lance le polling**
   - La jauge de progression apparaît
   - Polling toutes les 500ms vers `/core/sse-progress/<job_id>/`

3. **La tâche Celery traite les emails**
   - Pour chaque email envoyé
   - Mise à jour de `progress.update_progress()`
   - L'API REST retourne l'état actuel

4. **Le frontend affiche la progression**
   - Barre de progression mise à jour
   - Messages affichés en temps réel (latence 500ms max)
   - Statistiques actualisées

5. **Fin de l'envoi**
   - `progress.mark_as_completed()` appelé
   - Le polling détecte le statut "completed"
   - Arrêt du polling
   - Callback `onComplete` exécuté

---

## Configuration requise

### Django (aucune installation supplémentaire!)

Le système fonctionne avec Django standard, **pas besoin de**:
- ~~django-eventstream~~
- ~~django_grip.GripMiddleware~~
- ~~Configuration ASGI~~

### Celery

La tâche doit juste être enregistrée dans Celery normalement.

### URLs

Les URLs API doivent être incluses dans `heron/urls.py` (déjà fait):

```python
urlpatterns = [
    # ...
    path("core/", include(("apps.core.urls", "apps.core"), namespace="core")),
]
```

---

## Logs

Les logs restent identiques:
- `LOGGER_INVOICES` : Logs principaux d'envoi
- `LOGGER_EMAIL` : Logs spécifiques aux emails

Format des logs:
```
🚀 Début de l'envoi...
✅ [1/50] Email envoyé : CCT123 - FACTURE.pdf
❌ [2/50] Erreur email : CCT456 - FACTURE2.pdf : Invalid email
🎉 Envoi terminé : 48 succès, 2 erreur(s)
```

---

## Documentation complémentaire

**Documentation à jour:**
- `apps/core/README_PROGRESS.md` - Documentation complète du système de polling AJAX

**Exemple concret:**
- `apps/edi/templates/edi/edi_jauge_import.html`
- `apps/edi/views/views_jauges.py`
- `apps/edi/tasks.py`

---

## Auteur

Mis à jour par Paulo ALVES (via Claude Code)
Date : 2025-01-16
