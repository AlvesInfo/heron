# Système de progression AJAX - Référence Claude Code

## Description du système

Le projet Heron utilise un **système de polling AJAX** pour afficher des jauges de progression en temps réel lors de traitements longs (imports, exports, envois d'emails, etc.).

**Architecture:**
- Backend: Django + Celery + PostgreSQL
- Frontend: JavaScript (Vanilla) + Semantic UI
- Communication: Polling AJAX (500ms) vers API REST

**Avantages:**
- ✅ Aucune dépendance externe (pas de django-eventstream)
- ✅ Fonctionne avec Django WSGI standard
- ✅ Simple et fiable
- ✅ Interface Semantic UI cohérente

---

## Fichiers clés du système

### Documentation
- **`apps/core/README_PROGRESS.md`** - Documentation complète du système
- **`apps/core/TEMPLATES_PROGRESS.md`** - Templates de code prêts à l'emploi (⭐ UTILISER CELUI-CI pour générer du code)

### Code source
- **Modèle**: `apps/core/models/models_sse_progress.py` - Modèle `SSEProgress`
- **Vues API**: `apps/core/views/views_sse_progress.py` - Endpoints REST
- **URLs API**: `apps/core/urls.py` - Routes `/core/sse-progress/`
- **JavaScript**: `files/static/js/progress_polling.js` - Classe `ProgressPolling`

### Exemple de référence
- **Template**: `apps/edi/templates/edi/edi_jauge_import.html`
- **Vue**: `apps/edi/views/views_jauges.py` - Fonction `import_jauge()`
- **Tâche**: `apps/edi/tasks.py` - Fonction `task_test_import_jauge()`

---

## Quand utiliser ce système

Utiliser pour toute tâche longue (> 5 secondes):
- ✅ Import de fichiers EDI
- ✅ Envoi d'emails en masse
- ✅ Génération de rapports PDF
- ✅ Export de données
- ✅ Traitements batch
- ✅ Synchronisations

---

## Comment générer du code pour une nouvelle jauge

**IMPORTANT:** Utiliser les templates dans `apps/core/TEMPLATES_PROGRESS.md`

### Étape 1: Copier le template complet
Le fichier `TEMPLATES_PROGRESS.md` contient un template complet avec:
- Vue Django
- Tâche Celery
- Template HTML
- Configuration JavaScript
- URLs

### Étape 2: Remplacer les placeholders
- `[votre_app]` → nom de l'app Django
- `[nom_de_votre_vue]` → nom de la fonction de vue
- `[votre_tache]` → nom de la tâche Celery
- `[type_de_tache]` → type (ex: 'import', 'email_sending', 'export')
- `[votre_icone]` → icône Semantic UI ou emoji
- `[Titre de votre page]` → titre affiché

### Étape 3: Adapter la logique métier
Dans la tâche Celery, remplacer la boucle de traitement par la logique spécifique.

---

## Structure d'une implémentation complète

```
apps/[app]/
├── views/
│   └── [fichier].py          → Vue qui retourne job_id
├── tasks.py                   → Tâche Celery avec SSEProgress
├── templates/[app]/
│   └── [template].html        → HTML + JavaScript ProgressPolling
└── urls.py                    → Route vers la vue
```

---

## Pattern de code minimal

### Vue Django
```python
import uuid
from django.http import JsonResponse


def ma_vue(request):
    if request.method == "POST":
        job_id = str(uuid.uuid4())
        ma_tache.delay(job_id, request.user.id)
        return JsonResponse({"success": True, "job_id": job_id})
    return render(request, "template.html")
```

### Tâche Celery
```python
from celery import shared_task
from apps.core.models import SSEProgress


@shared_task(name="ma_tache")
def ma_tache(job_id, user_id):
    progress = SSEProgress.objects.create(
        job_id=job_id, user_id=user_id, task_type="mon_type", total_items=100
    )
    progress.mark_as_started()

    for i in range(100):
        # Traitement
        progress.update_progress(processed=1)

    progress.mark_as_completed()
```

### Template HTML (JavaScript)
```html
<div id="jauge"></div>
<script src="{% static 'js/progress_polling.js' %}"></script>
<script>
new ProgressPolling('jauge', data.job_id, {
    title: 'Mon traitement',
    icon: '📊',
    showDetails: true,
    onComplete: (r) => console.log('Terminé!', r)
});
</script>
```

---

## API REST disponible

Les endpoints suivants sont déjà implémentés dans `apps/core/`:

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/core/sse-progress/<job_id>/` | GET | État d'un job (utilisé par polling) |
| `/core/sse-progress/` | GET | Liste tous les jobs de l'utilisateur |
| `/core/sse-progress/active/` | GET | Liste jobs actifs uniquement |
| `/core/sse-progress/<job_id>/delete/` | DELETE | Supprimer un job terminé |

**Format de réponse pour le polling:**
```json
{
    "job_id": "abc-123",
    "status": "in_progress",
    "total_items": 100,
    "processed_items": 45,
    "failed_items": 0,
    "progress_percentage": 45,
    "current_message": "Traitement en cours...",
    "duration": 22.5
}
```

---

## Options JavaScript ProgressPolling

```javascript
new ProgressPolling(containerId, jobId, {
    // Affichage
    title: 'Titre',                // Titre de la jauge
    icon: '📊',                    // Icône (emoji ou Semantic UI)
    showDetails: true,             // Afficher stats détaillées (total, traités, restants)
    showStats: true,               // Afficher les messages de progression

    // Comportement
    pollInterval: 500,             // Intervalle de polling en ms (défaut: 500)
    autoHideOnComplete: false,     // Masquer automatiquement à la fin
    autoHideDelay: 3000,           // Délai avant masquage (si autoHide=true)
    debug: true,                   // Logs console pour debug

    // Callbacks
    onStart: (data) => {},         // Appelé au démarrage
    onProgress: (data) => {},      // Appelé à chaque mise à jour
    onComplete: (data) => {},      // Appelé à la fin
    onError: (error) => {}         // Appelé en cas d'erreur
});
```

---

## Méthodes du modèle SSEProgress

```python
# Création
progress = SSEProgress.objects.create(
    job_id=job_id, user_id=user_id, task_type="mon_type", total_items=100
)

# Démarrage
progress.mark_as_started()

# Mise à jour
progress.update_progress(
    processed=1,  # Nb items traités
    failed=0,  # Nb items échoués (optionnel)
    message="...",  # Message personnalisé (optionnel)
)

# Fin
progress.mark_as_completed()

# En cas d'erreur
progress.mark_as_failed("Message erreur")

# Propriétés disponibles
progress.progress_percentage  # Pourcentage (0-100)
progress.success_count  # Nb succès (processed - failed)
progress.status  # 'pending', 'in_progress', 'completed', 'failed'
progress.duration  # Durée en secondes
```

---

## Cas d'usage courants

Voir le fichier `apps/core/TEMPLATES_PROGRESS.md` pour des templates spécifiques:
- Import de fichiers
- Envoi d'emails en masse
- Export de données Excel
- Génération de rapports PDF
- Synchronisation de données

---

## Debugging

### Activer les logs JavaScript
```javascript
new ProgressPolling('jauge', job_id, { debug: true });
```

### Vérifier l'API manuellement
```bash
curl http://localhost:8000/core/sse-progress/[job_id]/
```

### Logs Python dans la tâche
```python
import logging

logger = logging.getLogger(__name__)
logger.info(f"Job {job_id}: traitement...")
```

---

## Checklist d'implémentation

Lorsque tu génères du code pour une nouvelle jauge:

1. [ ] Utiliser le template complet de `TEMPLATES_PROGRESS.md`
2. [ ] Créer la vue Django qui retourne `{'success': True, 'job_id': job_id}`
3. [ ] Créer la tâche Celery avec `SSEProgress`
4. [ ] Créer le template HTML avec `<div id="jauge"></div>`
5. [ ] Charger `{% static 'js/progress_polling.js' %}`
6. [ ] Initialiser `new ProgressPolling('jauge', data.job_id, {...})`
7. [ ] Ajouter la route dans `urls.py`
8. [ ] Tester avec `debug: true`

---

## Notes importantes

- Le modèle s'appelle `SSEProgress` (nom conservé pour compatibilité historique)
- MAIS le système utilise du polling AJAX, pas SSE
- Ne pas utiliser `SSEProgressTracker` (obsolète, système SSE ancien)
- Ne pas installer `django-eventstream` (obsolète)
- Le polling se fait automatiquement, pas besoin de code supplémentaire
- L'intervalle de 500ms est optimal pour la plupart des cas

---

## Références

**Documentation principale:** `apps/core/README_PROGRESS.md`

**Templates de code:** `apps/core/TEMPLATES_PROGRESS.md` ⭐

**Exemple fonctionnel complet:**
- `apps/edi/templates/edi/edi_jauge_import.html`
- `apps/edi/views/views_jauges.py`
- `apps/edi/tasks.py`