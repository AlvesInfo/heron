# Implémentation de la Progress Bar pour l'Import EDI

## Contexte

L'import EDI utilise `celery.group()` pour lancer plusieurs tâches en parallèle, ce qui est différent du pattern classique `.delay()`. Ce document explique comment adapter le système de progress bar pour ce cas spécifique.

---

## Architecture proposée

### Problème actuel
```python
# Dans celery_import_launch() - ligne 409
result = group(*tasks_list)().get(3600)  # Bloque jusqu'à la fin
```

Le `group()` lance toutes les tâches en parallèle mais attend la fin de toutes avant de retourner. On n'a pas de visibilité sur la progression en temps réel.

### Solution: Callback partagé

Chaque tâche du groupe mettra à jour le même `SSEProgress` via son `job_id`:
1. Créer le `SSEProgress` **avant** de lancer le groupe
2. Passer le `job_id` à chaque tâche
3. Chaque tâche met à jour la progression quand elle se termine
4. Le frontend poll l'API pour afficher la progression

---

## Modifications à effectuer

### 1. **Vue Django** - `apps/edi/views/views_imports.py`

#### Ligne 62-79: Modifier la gestion du POST

**Code actuel:**
```python
# Si l'on envoie un POST alors on lance l'import en tâche de fond celery
if request.method == "POST" and not in_action:
    bool_files = any([have_statment, have_monthly, have_retours, have_receptions, files_celery])

    # On vérifie qu'il y ait des fichiers
    if bool_files:
        user_pk = request.user.id

        if "bbgr_statment" in request.POST:
            import_launch_bbgr("bbgr_statment", user_pk)
        elif "bbgr_monthly" in request.POST:
            import_launch_bbgr("bbgr_monthly", user_pk)
        elif "bbgr_retours" in request.POST:
            import_launch_bbgr("bbgr_retours", user_pk)
        elif "bbgr_receptions" in request.POST:
            import_launch_bbgr("bbgr_receptions", user_pk)
        else:
            celery_import_launch(user_pk)

        in_action = True
```

**Code modifié:**
```python
# Si l'on envoie un POST alors on lance l'import en tâche de fond celery
if request.method == "POST" and not in_action:
    bool_files = any([have_statment, have_monthly, have_retours, have_receptions, files_celery])

    # On vérifie qu'il y ait des fichiers
    if bool_files:
        import uuid
        from django.http import JsonResponse

        user_pk = request.user.id
        job_id = str(uuid.uuid4())  # ← NOUVEAU: Générer un job_id

        if "bbgr_statment" in request.POST:
            import_launch_bbgr("bbgr_statment", user_pk, job_id)  # ← Passer job_id
        elif "bbgr_monthly" in request.POST:
            import_launch_bbgr("bbgr_monthly", user_pk, job_id)
        elif "bbgr_retours" in request.POST:
            import_launch_bbgr("bbgr_retours", user_pk, job_id)
        elif "bbgr_receptions" in request.POST:
            import_launch_bbgr("bbgr_receptions", user_pk, job_id)
        else:
            celery_import_launch(user_pk, job_id)  # ← Passer job_id

        # ← NOUVEAU: Retourner JSON avec job_id au lieu de recharger la page
        return JsonResponse({'success': True, 'job_id': job_id})
```

#### Imports à ajouter en haut du fichier:
```python
import uuid
from django.http import JsonResponse
```

---

### 2. **Fonction principale** - `apps/edi/loops/imports_loop_pool.py`

#### Ligne 379-430: Modifier `celery_import_launch()`

**Signature actuelle:**
```python
def celery_import_launch(user_pk: int):
```

**Nouvelle signature:**
```python
def celery_import_launch(user_pk: int, job_id: str):
```

**Modifications dans le corps de la fonction:**

```python
def celery_import_launch(user_pk: int, job_id: str):
    """Main pour lancement de l'import avec Celery"""

    # ← NOUVEAU: Importer SSEProgress
    from apps.core.models import SSEProgress

    active_action = None
    action = True
    progress = None  # ← NOUVEAU: Variable pour stocker l'objet progress

    try:
        tasks_list = []

        while action:
            active_action = get_action(action="import_edi_invoices")
            if not active_action.in_progress:
                action = False

        print("ACTION")

        # On initialise l'action comme en cours
        active_action.in_progress = True
        active_action.save()

        # ← NOUVEAU: Créer l'entrée SSEProgress AVANT de lancer les tâches
        proc_files_l = get_files_celery()
        total_files = len(proc_files_l)

        progress = SSEProgress.objects.create(
            job_id=job_id,
            user_id=user_pk,
            task_type='edi_import',
            total_items=total_files,
            custom_title='Import des factures EDI',
            completion_message=f'Import terminé : {total_files} fichiers traités'
        )
        progress.mark_as_started()

        start_all = time.time()

        # On boucle sur les fichiers à insérer
        for row_args in proc_files_l:
            tasks_list.append(
                celery_app.signature(
                    "suppliers_import",
                    kwargs={
                        "process_objects": row_args,
                        "user_pk": user_pk,
                        "job_id": job_id  # ← NOUVEAU: Passer job_id à chaque tâche
                    }
                )
            )

        # Lancer le groupe de tâches
        result = group(*tasks_list)().get(3600)
        print("result : ", result)
        LOGGER_EDI.warning(f"result : {result!r},\nin {time.time() - start_all} s")

        # Nettoyage SQL
        result_clean = group(
            *[celery_app.signature("sql_clean_general", kwargs={"start_all": start_all})]
        )().get(3600)

        print("result_clean : ", result_clean)
        LOGGER_EDI.warning(f"result_clean : {result_clean!r},\nin {time.time() - start_all} s")

        # ← NOUVEAU: Marquer comme terminé
        if progress:
            progress.mark_as_completed()

    except Exception as error:
        print("Error : ", error)
        LOGGER_EDI.exception(
            "Erreur détectée dans apps.edi.loops.imports_loop_pool.celery_import_launch()"
        )
        # ← NOUVEAU: Marquer comme échoué en cas d'erreur
        if progress:
            progress.mark_as_failed(str(error))

    finally:
        # On remet l'action en cours à False, après l'execution
        active_action.in_progress = False
        active_action.save()
```

#### Ligne 432-476: Modifier `import_launch_bbgr()`

**Signature actuelle:**
```python
def import_launch_bbgr(function_name: str, user_pk: int):
```

**Nouvelle signature:**
```python
def import_launch_bbgr(function_name: str, user_pk: int, job_id: str):
```

**Modifications similaires:**
```python
def import_launch_bbgr(function_name: str, user_pk: int, job_id: str):
    """Main pour lancement de l'import"""

    from apps.core.models import SSEProgress

    active_action = None
    action = True
    progress = None

    try:
        while action:
            active_action = get_action(action="import_edi_invoices")
            if not active_action.in_progress:
                action = False

        # ← NOUVEAU: Créer SSEProgress
        progress = SSEProgress.objects.create(
            job_id=job_id,
            user_id=user_pk,
            task_type='bbgr_import',
            total_items=1,  # Une seule tâche pour BBGR
            custom_title=f'Import BBGR {function_name}',
        )
        progress.mark_as_started()

        start_all = time.time()

        # On initialise l'action comme en cours
        active_action.in_progress = True
        active_action.save()

        result = group(
            *[
                celery_app.signature(
                    "bbgr_bi",
                    kwargs={
                        "function_name": function_name,
                        "user_pk": user_pk,
                        "job_id": job_id  # ← NOUVEAU: Passer job_id
                    }
                )
            ]
        )().get(3600)

        print("result : ", result)
        LOGGER_EDI.warning(f"result : {result!r},\nin {time.time() - start_all} s")

        result_clean = group(
            *[celery_app.signature("sql_clean_general", kwargs={"start_all": start_all})]
        )().get(3600)

        print("result_clean : ", result_clean)
        LOGGER_EDI.warning(f"result_clean : {result_clean!r},\nin {time.time() - start_all} s")

        # ← NOUVEAU: Marquer comme terminé
        if progress:
            progress.mark_as_completed()

    except Exception as error:
        print("Error : ", error)
        LOGGER_EDI.exception(
            "Erreur détectée dans apps.edi.loops.imports_loop_pool.import_launch_bbgr()"
        )
        # ← NOUVEAU: Marquer comme échoué
        if progress:
            progress.mark_as_failed(str(error))

    finally:
        # On remet l'action en cours à False, après l'execution
        active_action.in_progress = False
        active_action.save()
```

---

### 3. **Tâche Celery individuelle** - `apps/edi/imports/imports_suppliers_invoices_pool.py`

**IMPORTANT:** Chaque tâche Celery (par exemple `suppliers_import`) doit être modifiée pour:
1. Accepter le paramètre `job_id`
2. Mettre à jour la progression quand elle se termine

**Exemple de modification de la signature de la tâche:**

```python
@celery_app.task(name="suppliers_import", bind=True)
def suppliers_import(self, process_objects, user_pk, job_id=None):  # ← NOUVEAU: job_id optionnel
    """
    Tâche d'import d'un fichier fournisseur
    """
    try:
        # ... votre code d'import existant ...

        # ← NOUVEAU: À la fin, mettre à jour la progression
        if job_id:
            from apps.core.models import SSEProgress
            from django.db import transaction

            with transaction.atomic():
                progress = SSEProgress.objects.select_for_update().get(job_id=job_id)
                progress.update_progress(
                    processed=1,
                    message=f"Fichier {process_objects[2]} importé"
                )

        return {"status": "success", "file": process_objects[2]}

    except Exception as e:
        # ← NOUVEAU: En cas d'erreur, compter comme failed
        if job_id:
            from apps.core.models import SSEProgress
            from django.db import transaction

            with transaction.atomic():
                progress = SSEProgress.objects.select_for_update().get(job_id=job_id)
                progress.update_progress(
                    processed=1,
                    failed=1,
                    message=f"Erreur fichier {process_objects[2]}: {str(e)}"
                )

        return {"status": "error", "file": process_objects[2], "error": str(e)}
```

**Note importante:** Le `select_for_update()` est crucial pour éviter les race conditions quand plusieurs tâches mettent à jour le même `SSEProgress` simultanément.

---

### 4. **Template HTML** - `apps/edi/templates/edi/edi_import.html`

#### Modifier pour utiliser AJAX et afficher la jauge

**Ajouter dans le `<head>` ou avant `</body>`:**
```html
<div id="jauge" style="margin-top: 20px;"></div>
```

**Dans le bloc `{% block script %}`:**

```html
{% block script %}
<script src="{% static 'js/progress_polling.js' %}"></script>
<script>
$(document).ready(function() {
    // Gérer le clic sur le bouton d'import
    $('form').on('submit', async function(e) {
        e.preventDefault();  // Empêcher le rechargement de la page

        const form = $(this);
        const formData = new FormData(this);

        try {
            // Envoyer la requête POST
            const response = await fetch(window.location.href, {
                method: 'POST',
                body: formData,
            });

            const data = await response.json();

            if (data.success) {
                // Masquer le formulaire
                form.hide();

                // Afficher la jauge de progression
                new ProgressPolling('jauge', data.job_id, {
                    title: 'Import des factures EDI',
                    icon: '📁',
                    showDetails: true,
                    showStats: true,
                    pollInterval: 1000,  // Polling toutes les 1s (plusieurs fichiers)
                    debug: true,
                    onComplete: (result) => {
                        console.log('✅ Import terminé!', result);
                        // Recharger la page après 3s
                        setTimeout(() => {
                            window.location.reload();
                        }, 3000);
                    },
                    onError: (error) => {
                        console.error('❌ Erreur:', error);
                        alert('Une erreur est survenue lors de l\'import');
                        window.location.reload();
                    }
                });
            }
        } catch (error) {
            console.error('Erreur:', error);
            alert('Erreur de communication avec le serveur');
        }
    });
});
</script>
{% endblock %}
```

---

## Résumé des modifications

### Fichiers modifiés:

1. ✅ **`apps/edi/views/views_imports.py`** - COMPLÉTÉ
   - ✅ Ajout imports: `uuid`, `JsonResponse`
   - ✅ Génération `job_id` dans le POST
   - ✅ Passage `job_id` aux fonctions `celery_import_launch()` et `import_launch_bbgr()`
   - ✅ Retour JSON au lieu de recharger la page

2. ✅ **`apps/edi/loops/imports_loop_pool.py`** - COMPLÉTÉ
   - ✅ Modification signature de `celery_import_launch(user_pk, job_id)`
   - ✅ Création `SSEProgress` avant le `group()`
   - ✅ Passage `job_id` à chaque tâche du groupe
   - ✅ Marquage completed/failed à la fin
   - ✅ Même modifications pour `import_launch_bbgr()`

3. ✅ **`apps/edi/tasks.py`** - COMPLÉTÉ
   - ✅ Ajout paramètre `job_id=None` aux tâches `launch_suppliers_import()` et `launch_bbgr_bi_import()`
   - ✅ Mise à jour `SSEProgress` à la fin de chaque tâche
   - ✅ Utilisation `select_for_update()` pour éviter race conditions
   - ✅ Gestion des erreurs avec `failed=1`

4. ✅ **`apps/edi/templates/edi/edi_import.html`** - COMPLÉTÉ
   - ✅ Suppression des anciens click handlers
   - ✅ Suppression de la logique de rechargement automatique
   - ✅ Chargement `progress_polling.js`
   - ✅ Ajout gestionnaire unifié pour soumission AJAX du formulaire
   - ✅ Affichage de la jauge de progression après soumission

5. ✅ **`apps/edi/templates/edi/edi_import_table.html`** - COMPLÉTÉ
   - ✅ Ajout `<div id="progress-container"></div>` pour la jauge

---

## Avantages de cette approche

✅ **Pas de modification du pattern `group()`** - On garde la structure existante
✅ **Suivi en temps réel** - Chaque tâche met à jour la progression
✅ **Thread-safe** - `select_for_update()` évite les race conditions
✅ **Gestion d'erreurs** - Compte les fichiers en erreur
✅ **Réutilisable** - Même pattern pour `import_launch_bbgr()`

---

## Points d'attention

⚠️ **Race conditions:** Utiliser **obligatoirement** `select_for_update()` dans les tâches Celery pour éviter que plusieurs tâches n'écrasent les mises à jour

⚠️ **Interval de polling:** Avec plusieurs fichiers en parallèle, utiliser `pollInterval: 1000` (1s) au lieu de 500ms pour réduire la charge

⚠️ **Timeout:** Le `group().get(3600)` attend 1h max. Si vos imports sont plus longs, augmenter ce timeout

⚠️ **Migration:** Ne pas oublier de créer et appliquer la migration pour les nouveaux champs du modèle:
```bash
python manage.py makemigrations core
python manage.py migrate core
```

---

## Test de l'implémentation

1. **Lancer un import avec un seul fichier:**
   - Vérifier que la jauge apparaît
   - Vérifier que "1/1" s'affiche
   - Vérifier le message final

2. **Lancer un import avec plusieurs fichiers:**
   - Vérifier que le compteur augmente au fur et à mesure
   - Vérifier que les fichiers s'affichent dans le message

3. **Simuler une erreur:**
   - Ajouter un fichier invalide
   - Vérifier que la colonne "Erreurs" apparaît
   - Vérifier le message final avec le nombre d'erreurs

---

## Alternative: Pattern Chord

Si vous voulez un callback unique à la fin de toutes les tâches, vous pouvez utiliser `chord()`:

```python
from celery import chord

# Au lieu de group()
callback = celery_app.signature("import_complete_callback", kwargs={"job_id": job_id})
result = chord(tasks_list)(callback).get(3600)
```

Avec une tâche callback:
```python
@celery_app.task(name="import_complete_callback")
def import_complete_callback(results, job_id):
    from apps.core.models import SSEProgress
    progress = SSEProgress.objects.get(job_id=job_id)
    progress.mark_as_completed()
    return results
```

Mais cette approche ne permet pas de suivre la progression en temps réel (seulement à la fin).

---

## 🎉 Implémentation Complétée

**Date de complétion:** 2025-11-16

L'implémentation de la progress bar pour l'import EDI est maintenant **complète**. Tous les fichiers ont été modifiés avec succès.

### Prochaines étapes

1. **Tester l'implémentation:**
   - Lancer un import EDI avec plusieurs fichiers
   - Vérifier que la jauge s'affiche correctement
   - Vérifier que le compteur progresse en temps réel
   - Tester les différents types d'imports (EDI, BBGR statment, monthly, retours, receptions)

2. **Vérifier les erreurs:**
   - Tester avec un fichier invalide
   - Vérifier que la colonne "Erreurs" apparaît
   - Vérifier le message final avec le nombre d'erreurs

3. **Optimisations possibles (optionnel):**
   - Ajuster le `pollInterval` si nécessaire (actuellement 1000ms)
   - Personnaliser les messages de progression dans les tâches
   - Ajuster le délai de rechargement après completion (actuellement 3s)

### Rappel des fonctionnalités implémentées

✅ Soumission AJAX sans rechargement de page
✅ Progress bar en temps réel avec polling
✅ Compteur de fichiers traités / total
✅ Compteur d'erreurs (masqué si 0)
✅ Durée arrondie à la seconde
✅ Messages personnalisés par type d'import
✅ Thread-safety pour les tâches parallèles
✅ Gestion des 5 types d'imports différents
✅ Rechargement automatique après succès