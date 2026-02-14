# Notifications utilisateur - Documentation

## Vue d'ensemble

Systeme de notifications internes pour HERON. Une icone cloche dans le menu affiche un point rouge quand des notifications non lues existent. Au clic, un panneau deroulant affiche la liste des notifications chargees dynamiquement via AJAX.

---

## Architecture

```
apps/core/
    models/models_notifications.py   # Modele Notification (BDD)
    bin/notifications.py             # CRUD (creation, lecture, marquage, suppression)
    views/views_notifications.py     # Endpoints API JSON
    urls.py                          # Routes /core/notifications/...

heron/
    processors.py                    # Context processor (compteur badge)
    templates/heron/menu_user.html   # HTML cloche + panneau

files/static/js/notifications.js     # JavaScript (AJAX, polling, affichage)
```

---

## Modele Notification

| Champ | Type | Description |
|-------|------|-------------|
| `uuid_identification` | UUIDField (PK) | Identifiant unique |
| `user` | FK → User | Destinataire (CASCADE) |
| `created_by` | FK → User | Emetteur optionnel (SET_NULL) |
| `title` | CharField(255) | Titre de la notification |
| `message` | TextField | Contenu detaille |
| `level` | CharField | `info`, `warning`, `error`, `success` |
| `is_read` | BooleanField | Flag lecteur (defaut: False) |
| `read_at` | DateTimeField | Date/heure de lecture |
| `link` | CharField(500) | URL de navigation optionnelle |
| `created_at` | DateTimeField | Date de creation (auto) |
| `modified_at` | DateTimeField | Date de modification (auto) |

**Index composites** : `(user, is_read)` et `(user, -created_at)` pour la performance.

**Niveaux et icones** :

| Level | Icone Semantic UI | Couleur |
|-------|-------------------|---------|
| `info` | info circle | blue |
| `warning` | exclamation triangle | yellow |
| `error` | times circle | red |
| `success` | check circle | green |

---

## Envoyer une notification

### Depuis n'importe ou dans le code Python

```python
from apps.core.bin.notifications import create_notification

# Notification simple
create_notification(
    user=destinataire,       # objet User (obligatoire)
    title="Titre",           # str (obligatoire)
    message="Contenu",       # str (obligatoire)
)

# Notification complete avec tous les parametres
create_notification(
    user=destinataire,       # objet User
    title="Import termine",  # titre court
    message="245 lignes importees avec succes.",  # detail
    level="success",         # info | warning | error | success
    link="/import/resultats/",  # URL vers laquelle naviguer au clic
    created_by=request.user, # l'utilisateur qui a declenche l'action
)
```

### Exemples concrets

```python
from apps.core.bin.notifications import create_notification
from apps.users.models import User

# Notifier un utilisateur apres un import
def post_import(request, nb_lignes):
    create_notification(
        user=request.user,
        title="Import termine",
        message=f"{nb_lignes} lignes importees.",
        level="success",
        link="/data_flux/imports/",
        created_by=request.user,
    )

# Notifier un administrateur d'une erreur
def notifier_erreur(message_erreur):
    for admin in User.objects.filter(is_superuser=True):
        create_notification(
            user=admin,
            title="Erreur systeme",
            message=message_erreur,
            level="error",
        )

# Notifier plusieurs utilisateurs
def notifier_groupe(users, titre, message):
    for user in users:
        create_notification(user=user, title=titre, message=message)
```

---

## Fonctions CRUD disponibles

Toutes les fonctions sont dans `apps.core.bin.notifications` :

```python
from apps.core.bin.notifications import (
    create_notification,        # Creer une notification
    get_unread_notifications,   # QuerySet des non lues
    get_unread_count,           # Nombre de non lues (int)
    get_all_notifications,      # Toutes les notifications (limit=50)
    mark_notification_as_read,  # Marquer une notification comme lue
    mark_all_as_read,           # Marquer toutes comme lues
    delete_notification,        # Supprimer une notification
)
```

### Details

| Fonction | Parametres | Retour |
|----------|-----------|--------|
| `create_notification(user, title, message, level, link, created_by)` | user, title, message obligatoires | objet Notification |
| `get_unread_notifications(user)` | user | QuerySet |
| `get_unread_count(user)` | user | int |
| `get_all_notifications(user, limit=50)` | user, limit optionnel | QuerySet |
| `mark_notification_as_read(notification_uuid, user)` | uuid, user | True/False |
| `mark_all_as_read(user)` | user | int (nb modifiees) |
| `delete_notification(notification_uuid, user)` | uuid, user | True/False |

---

## API JSON

Toutes les routes sont sous `/core/` et necessitent une authentification.

### GET /core/notifications/

Liste des notifications de l'utilisateur connecte.

**Parametre optionnel** : `?limit=50`

**Reponse** :
```json
{
    "unread_count": 3,
    "notifications": [
        {
            "uuid": "5aa87d5b-96a6-4d4c-8bf2-561be286893b",
            "title": "Import termine",
            "message": "245 lignes importees.",
            "level": "success",
            "level_icon": "check circle",
            "level_color": "green",
            "is_read": false,
            "link": "/import/resultats/",
            "time_since": "il y a 5 min",
            "created_at": "2025-02-14T14:41:00+00:00"
        }
    ]
}
```

### POST /core/notifications/mark-read/`<uuid>`/

Marque une notification comme lue.

**Reponse** : `{"success": true, "unread_count": 2}`

### POST /core/notifications/mark-all-read/

Marque toutes les notifications comme lues.

**Reponse** : `{"success": true, "unread_count": 0}`

### POST /core/notifications/delete/`<uuid>`/

Supprime une notification.

**Reponse** : `{"success": true, "unread_count": 2}`

---

## Fonctionnement cote navigateur

1. **Chargement de la page** : le context processor `unread_notifications_count` injecte le compteur dans le template. Si > 0, le point rouge sur la cloche est visible.

2. **Clic sur la cloche** : le JavaScript fait un GET AJAX vers `/core/notifications/`, recoit le JSON, et affiche les notifications dans le panneau.

3. **Clic sur une notification** : POST AJAX vers `/core/notifications/mark-read/<uuid>/`. La notification passe en lue (style normal). Si elle a un `link`, navigation vers cette URL.

4. **"Tout marquer lu"** : POST AJAX vers `/core/notifications/mark-all-read/`. Le point rouge disparait.

5. **Polling automatique** : toutes les 60 secondes, le compteur est rafraichi en arriere-plan. Si de nouvelles notifications arrivent, le point rouge apparait sans recharger la page.

6. **Fermeture** : clic en dehors du panneau le ferme automatiquement.

---

## CSRF

Le token CSRF est gere globalement par `base_html_foot.js` via `$.ajaxSetup`. Aucune configuration supplementaire n'est necessaire pour les appels POST.

---

## Fichiers modifies lors de l'installation

| Fichier | Modification |
|---------|-------------|
| `apps/core/models/__init__.py` | Import de `models_notifications` |
| `apps/core/views/__init__.py` | Import de `views_notifications` |
| `apps/core/urls.py` | 4 routes notifications |
| `heron/processors.py` | Fonction `unread_notifications_count` |
| `heron/settings/base.py` | Ajout du context processor |
| `heron/templates/heron/menu_user.html` | Cloche + panneau |
| `heron/templates/heron/base_semantic.html` | Chargement de `notifications.js` |
