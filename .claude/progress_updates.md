# Mises à jour récentes du système de progression

## Date: 2025-01-16

### Nouvelles fonctionnalités ajoutées

#### 1. **Compteur d'erreurs automatique**
- Affiche une 4ème colonne "Erreurs" (rouge) dans les statistiques
- Masquée par défaut, apparaît uniquement s'il y a des erreurs
- Mise à jour en temps réel

**Code dans la tâche Celery:**
```python
progress.update_progress(
    processed=1,
    failed=1,  # Compteur d'erreurs
    message="Erreur sur l'item X"
)
```

**Affichage:**
- Grid passe de 3 colonnes à 4 colonnes
- Total | Traités | Restants | Erreurs (masquée si 0)

#### 2. **Durée arrondie**
- La durée est automatiquement arrondie à la seconde (pas de virgules)
- `Math.round(data.duration)` dans le JavaScript
- Affichage: `"Terminé avec succès ! (13s)"`

#### 3. **Messages et titres personnalisés depuis le backend**

Nouveaux champs dans le modèle `SSEProgress`:
- `custom_title` (CharField, 200 max, optionnel) - Titre personnalisé de la jauge
- `completion_message` (CharField, 500 max, optionnel) - Message final personnalisé

**Utilisation:**
```python
progress = SSEProgress.objects.create(
    job_id=job_id,
    user_id=user_id,
    task_type='import',
    total_items=100,
    custom_title='Import de fichiers EDI',
    completion_message='Import terminé : 98 fichiers importés avec succès!'
)
```

**Comportement JavaScript:**
- Si `completion_message` existe → afficher ce message
- Sinon → message par défaut avec durée et erreurs

#### 4. **Format du message final par défaut**
- Sans erreurs: `"Terminé avec succès ! (12s)"`
- Avec erreurs: `"Terminé avec succès ! (12s) - 3 erreurs"` (ou "1 erreur")

---

## Fichiers modifiés

### Backend
1. **`apps/core/models/models_sse_progress.py`**
   - Ajout de `custom_title` (CharField)
   - Ajout de `completion_message` (CharField)
   - Mise à jour de `to_dict()` pour inclure ces champs

2. **Migration nécessaire:**
   ```bash
   python manage.py makemigrations core
   python manage.py migrate core
   ```

### Frontend
3. **`files/static/js/progress_polling.js`**
   - Grid: 3 → 4 colonnes (ajout colonne Erreurs)
   - Références: `errors` et `errorsContainer` ajoutées dans `this.elements`
   - Logique d'affichage/masquage automatique des erreurs
   - Durée arrondie avec `Math.round()`
   - Support de `completion_message` personnalisé

### Documentation
4. **`apps/core/TEMPLATES_PROGRESS.md`**
   - Nouvelle section "Fonctionnalités automatiques de la jauge"
   - Documentation du compteur d'erreurs
   - Documentation de la durée arrondie
   - Documentation des messages personnalisés
   - Exemples de code mis à jour

5. **`.claude/progress_system_code.yaml`**
   - À METTRE À JOUR avec les nouveaux champs du modèle
   - À METTRE À JOUR avec le nouveau code JavaScript

---

## Exemple complet d'utilisation

### Tâche Celery avec gestion d'erreurs
```python
@shared_task(name="import_fichiers")
def import_fichiers(job_id, user_id, fichiers):
    progress = SSEProgress.objects.create(
        job_id=job_id,
        user_id=user_id,
        task_type='file_import',
        total_items=len(fichiers),
        custom_title='Import de fichiers EDI',
        completion_message='Import terminé !'  # Message personnalisé (optionnel)
    )

    progress.mark_as_started()

    for idx, fichier in enumerate(fichiers, 1):
        try:
            importer_fichier(fichier)
            progress.update_progress(
                processed=1,
                message=f"Fichier {idx}/{len(fichiers)} importé"
            )
        except Exception as e:
            # En cas d'erreur sur un fichier
            progress.update_progress(
                processed=1,
                failed=1,  # ← Compteur d'erreurs
                message=f"Erreur fichier {idx}: {str(e)}"
            )

    progress.mark_as_completed()
    # Si completion_message n'était pas défini:
    # Affichera: "Terminé avec succès ! (45s) - 2 erreurs"
    # Si completion_message défini:
    # Affichera: "Import terminé !"

    return {"status": "success", "job_id": job_id}
```

### Template HTML (utilisation du titre depuis le contexte Django)
```html
<script>
new ProgressPolling('jauge', data.job_id, {
    title: '{{ progress_title|default:"Import de fichiers" }}',
    icon: '📁',
    showDetails: true,  // Affiche Total/Traités/Restants/Erreurs
    showStats: true,
    debug: true
});
</script>
```

---

## API Response (exemple)

Avec les nouveaux champs, l'API retourne:
```json
{
    "job_id": "abc-123",
    "status": "completed",
    "total_items": 100,
    "processed_items": 100,
    "failed_items": 2,
    "progress_percentage": 100,
    "duration": 45.6789,
    "custom_title": "Import de fichiers EDI",
    "completion_message": "Import terminé !",
    "current_message": "Fichier 100/100 importé"
}
```

JavaScript affichera:
- Durée: `46s` (arrondie)
- Message: `"Import terminé !"` (ou message par défaut avec erreurs si non défini)
- Colonne Erreurs: Visible avec `2` (rouge)

---

## À faire par l'utilisateur

1. **Créer et appliquer la migration:**
   ```bash
   python manage.py makemigrations core
   python manage.py migrate core
   ```

2. **Tester avec une tâche:**
   - Créer une tâche avec `failed=1` pour voir le compteur d'erreurs
   - Vérifier que la durée est bien arrondie
   - Tester avec et sans `completion_message`

3. **Mettre à jour les tâches existantes (optionnel):**
   - Ajouter `custom_title` et `completion_message` si désiré
   - Ajouter la gestion d'erreurs avec `failed=1`