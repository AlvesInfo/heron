# Envoi d'emails avec suivi SSE en temps réel

## Vue d'ensemble

Ce système permet d'envoyer des factures par email via l'API Gmail avec un suivi de progression en temps réel grâce à SSE (Server-Sent Events).

## Architecture

### Backend

- **Tâche Celery**: `apps/invoices/bin/api_gmail/tasks_gmail_sse.py`
  - `launch_celery_send_invoice_mails_gmail_sse()` - Tâche principale d'envoi
  - `prepare_invoice_email_data()` - Préparation des données email

- **Vues Django**: `apps/invoices/bin/api_gmail/views_sse.py`
  - `send_invoices_emails_sse()` - Page principale avec formulaire
  - `send_invoices_progress_sse()` - Page de progression uniquement

- **URLs**: `apps/invoices/urls.py`
  - `/invoices/send_invoices_sse/` - Page d'envoi
  - `/invoices/send_invoices_progress_sse/<job_id>/` - Page de progression

### Frontend

- **Templates**:
  - `apps/invoices/templates/invoices/send_invoices_sse.html` - Interface principale
  - `apps/invoices/templates/invoices/send_invoices_progress_sse.html` - Progression

### Système SSE générique

- **Modèle DB**: `apps/core/models/models_sse_progress.py` - Modèle `SSEProgress`
- **Tracker**: `apps/core/bin/sse_progress.py` - Classe `SSEProgressTracker`
- **JavaScript**: `files/static/js/sse_progress.js` - Classe `SSEProgressUI`

## Utilisation

### 1. Accéder à la page

```
http://votre-domaine.com/invoices/send_invoices_sse/
```

### 2. Paramètres optionnels

- **CCT** : Filtrer par CCT spécifique (laisser vide pour tous)
- **Période** : Filtrer par période au format `YYYY-MM` (laisser vide pour toutes)

### 3. Suivi en temps réel

Une fois l'envoi lancé, la jauge de progression affiche en temps réel :

- **Barre de progression** : Pourcentage d'avancement
- **Détails** : Total, traités, restants
- **Messages** : Pour chaque email envoyé
  ```
  ✅ Email 1/50 envoyé : CCT123 - FACTURE_2025_01.pdf → email1@example.com, email2@example.com
  ```
- **Statistiques** : Vitesse d'envoi, temps écoulé

### 4. Messages d'événements

Le système affiche des messages détaillés pour chaque email :

#### Succès
```
✅ Email {i}/{total} envoyé : {cct} - {fichier} → {destinataires}
```

#### Erreur
```
⚠️ Email {i}/{total} ERREUR : {cct} - {fichier} : {message_erreur}
```

#### Fin
```
✅ Envoi terminé : {succès} succès, {erreurs} erreur(s) sur {total} facture(s)
```

## Fonctionnalités

### ✅ Temps réel instantané
- Pas de polling HTTP
- Connexion SSE persistante
- Latence < 100ms

### ✅ Affichage détaillé
- Nom du CCT
- Nom du fichier PDF
- Liste des destinataires (2 premiers affichés)
- Statut de chaque envoi

### ✅ Gestion des erreurs
- Continue l'envoi même en cas d'erreur
- Affiche les erreurs sans bloquer
- Trace en base de données

### ✅ Persistance
- État sauvegardé en base de données
- Récupération possible après rafraîchissement
- Historique des envois

## Exemple de flux

1. **L'utilisateur clique sur "Envoyer les factures"**
   - Le formulaire est caché
   - La jauge SSE apparaît

2. **La tâche Celery démarre**
   - Création du job SSE en DB
   - Événement SSE `start` envoyé

3. **Pour chaque facture**
   - Email envoyé via Gmail API
   - Progression mise à jour en DB
   - Événement SSE `progress` envoyé avec le message détaillé
   - Message affiché dans le navigateur en temps réel

4. **Fin de l'envoi**
   - Événement SSE `complete` envoyé
   - Statistiques finales affichées
   - Option de rechargement ou redirection

## Configuration requise

### Django settings

```python
INSTALLED_APPS = [
    # ...
    'django_eventstream',  # Pour SSE
]

MIDDLEWARE = [
    # ...
    'django_grip.GripMiddleware',  # Après SessionMiddleware
]
```

### Celery

La tâche doit être enregistrée dans Celery :

```python
# apps/invoices/bin/api_gmail/tasks_gmail_sse.py
@shared_task(name="celery_send_invoices_emails_gmail_sse")
def launch_celery_send_invoice_mails_gmail_sse(user_pk, cct=None, period=None):
    ...
```

### URLs

Les URLs SSE core doivent être incluses dans `heron/urls.py` :

```python
urlpatterns = [
    # ...
    path("core/", include(("apps.core.urls", "apps.core"), namespace="core")),
]
```

## Logs

Les logs sont écrits dans :
- `LOGGER_INVOICES` : Logs principaux d'envoi
- `LOGGER_EMAIL` : Logs spécifiques aux emails

Format des logs :
```
🚀 Début de l'envoi...
✅ [1/50] Email envoyé : CCT123 - FACTURE.pdf
❌ [2/50] Erreur email : CCT456 - FACTURE2.pdf : Invalid email
🎉 Envoi terminé : 48 succès, 2 erreur(s)
```

## Documentation complémentaire

- **Système SSE générique** : `apps/core/README_SSE.md`
- **Guide d'intégration SSE** : `apps/core/GUIDE_INTEGRATION_SSE.md`
- **Démarrage rapide SSE** : `apps/core/DEMARRAGE_RAPIDE_SSE.md`

## Auteur

Créé par Paulo ALVES (via Claude Code)
Date : 2025-01-10