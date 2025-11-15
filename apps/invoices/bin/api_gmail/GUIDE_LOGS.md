# Guide complet des Logs et Traces

## 🎯 Vue d'ensemble

Le nouveau système conserve **TOUS les logs** de l'ancien système SMTP, et en ajoute même plus! Voici où les trouver.

---

## 📊 Types de logs disponibles

### 1. ✅ Traces en base de données (comme avant)

Chaque email envoyé crée une trace avec `get_trace()` exactement comme l'ancien système.

#### Ce qui est tracé pour chaque email:

```python
trace = get_trace(
    trace_name="Send invoices mail (Gmail API)",  # ou "...ERROR..." en cas d'erreur
    file_name=str(file_path),                      # ex: "facture_CCT_2025-01.pdf"
    application_name="invoices_send_by_email_gmail",
    flow_name="send_invoice_email_gmail",
    comment="Email envoyé avec succès à client@example.com (Message ID: 18d2abc...)",
)
trace.created_by = user                            # Utilisateur qui a lancé
trace.time_to_process = 0.8  # Temps d'envoi en secondes
trace.save()
```

#### Où voir ces traces?

Dans votre application Django, là où vous consultiez les traces avant :
- Modèle : `apps.data_flux.models.Trace` (probablement)
- Admin Django : `/admin/data_flux/trace/`
- Ou votre interface custom de traces

**Filtres utiles :**
```python
# Dans Django shell ou vos vues
from apps.data_flux.models import Trace

# Traces d'envoi Gmail
traces_gmail = Trace.objects.filter(
    application_name="invoices_send_by_email_gmail"
).order_by('-created_at')

# Erreurs uniquement
traces_erreurs = Trace.objects.filter(
    application_name="invoices_send_by_email_gmail",
    errors=True
).order_by('-created_at')

# Traces du jour
from django.utils import timezone
from datetime import timedelta
today = timezone.now().date()
traces_today = Trace.objects.filter(
    application_name="invoices_send_by_email_gmail",
    created_at__date=today
)

# Stats
print(f"Total: {traces_gmail.count()}")
print(f"Erreurs: {traces_erreurs.count()}")
print(f"Aujourd'hui: {traces_today.count()}")
```

---

### 2. 📝 Logs Python (LOGGER_INVOICES et LOGGER_EMAIL)

Comme l'ancien système, chaque email est loggué via les loggers Python.

#### Où voir ces logs?

**Selon votre configuration dans `heron/settings.py` :**

```python
# Exemple de configuration typique
LOGGING = {
    'handlers': {
        'file_invoices': {
            'filename': '/path/to/logs/invoices.log',  # ← Vérifiez ce chemin
        },
        'file_email': {
            'filename': '/path/to/logs/email.log',     # ← Vérifiez ce chemin
        },
    },
}
```

**Commandes pour voir les logs :**

```bash
# Logs d'envoi en temps réel
tail -f /path/to/logs/invoices.log

# Logs des 100 dernières lignes
tail -100 /path/to/logs/invoices.log

# Rechercher les erreurs
grep -i "error\|erreur" /path/to/logs/invoices.log

# Logs d'aujourd'hui
grep "$(date +%Y-%m-%d)" /path/to/logs/invoices.log

# Compter les emails envoyés aujourd'hui
grep "$(date +%Y-%m-%d)" /path/to/logs/invoices.log | grep -c "envoyé avec succès"
```

**Exemple de logs générés :**

```log
2025-01-10 14:32:15 [INFO] Début de l'envoi de 500 factures via l'API Gmail (task_id: abc-123, job_id: xyz-789, utilisateur: 1)
2025-01-10 14:32:16 [INFO] Email 1/500 envoyé avec succès: facture_CCT_001_2025-01.pdf (Message ID: 18d2abc123def456, durée: 0.8s)
2025-01-10 14:32:17 [INFO] Email 2/500 envoyé avec succès: facture_CCT_002_2025-01.pdf (Message ID: 18d2abc789ghi012, durée: 0.7s)
2025-01-10 14:32:18 [ERROR] Erreur email 3/500: facture_CCT_003_2025-01.pdf - Quota exceeded (durée: 0.5s)
...
2025-01-10 14:35:42 [INFO] Envoi terminé (task_id: abc-123, job_id: xyz-789): 498 succès, 2 erreurs sur 500 emails (temps total: 207.3s, moyenne: 2.4 emails/s)
```

---

### 3. 🌸 Logs Celery (visibles dans Flower)

**C'est nouveau et encore plus détaillé !**

Les logs Celery utilisent `celery_logger` et sont **ultra-détaillés** avec des émojis pour faciliter la lecture.

#### Installation de Flower (interface web pour Celery)

```bash
cd /Users/paulo/SitesWeb/heron
source .venv/bin/activate

# Installer Flower
pip install flower

# Lancer Flower
celery -A heron flower --port=5555

# Ou en arrière-plan
nohup celery -A heron flower --port=5555 > /tmp/flower.log 2>&1 &
```

#### Accès à Flower

Ouvrez votre navigateur : **http://localhost:5555**

#### Que voir dans Flower?

**1. Dashboard :**
- Nombre de tâches en cours
- Nombre de tâches réussies/échouées
- Graphiques en temps réel

**2. Tasks :**
- Liste de toutes les tâches
- Rechercher par nom : `celery_send_invoices_emails_gmail_enhanced`
- Filtrer par état : SUCCESS, FAILURE, PENDING, etc.

**3. Logs détaillés d'une tâche :**

Cliquez sur une tâche → Onglet "Details" → Voir tous les logs :

```log
================================================================================
DÉMARRAGE ENVOI FACTURES VIA API GMAIL
================================================================================
Task ID: abc-123-def-456
Job ID: xyz-789-ghi-012
Utilisateur: 1
CCT: Tous
Période: Toutes
================================================================================
📧 Template email chargé: 'Vos factures du mois'
🔍 Filtre: Toutes les factures non envoyées
⏳ Préparation de la liste des emails...
================================================================================
📊 RÉSUMÉ AVANT ENVOI
================================================================================
Total d'emails à envoyer: 500
================================================================================
--------------------------------------------------------------------------------
📧 EMAIL 1/500
--------------------------------------------------------------------------------
CCT: CCT001
Fichier: facture_CCT_001_2025-01.pdf
Destinataires: client1@example.com, compta1@example.com
✅ SUCCESS - Email 1/500 envoyé en 0.82s
   Message ID: 18d2abc123def456
   Destinataire(s): client1@example.com, compta1@example.com
--------------------------------------------------------------------------------
📧 EMAIL 2/500
--------------------------------------------------------------------------------
CCT: CCT002
Fichier: facture_CCT_002_2025-01.pdf
Destinataires: client2@example.com
✅ SUCCESS - Email 2/500 envoyé en 0.73s
   Message ID: 18d2abc789ghi012
   Destinataire(s): client2@example.com
[...]
================================================================================
📊 PROGRESSION: 10/500 emails (2%)
   Succès: 9 | Erreurs: 1
   Vitesse: 12.3 emails/s
   Temps restant estimé: 0m 40s
================================================================================
[...]
================================================================================
🏁 ENVOI TERMINÉ
================================================================================
Task ID: abc-123-def-456
Job ID: xyz-789-ghi-012
Total emails: 500
✅ Succès: 498 (99.6%)
❌ Erreurs: 2 (0.4%)
⏱️  Temps total: 3m 27s
⚡ Vitesse moyenne: 2.4 emails/s
================================================================================
```

**4. Worker monitoring :**
- État des workers Celery
- Nombre de tâches en cours par worker
- Charge CPU/mémoire

---

## 🔍 Comparaison Ancien vs Nouveau

| Type de log | Ancien système (SMTP) | ✅ Nouveau système (API Gmail) |
|-------------|----------------------|-------------------------------|
| **Trace DB par email** | ✅ Oui | ✅ Oui (identique) |
| **LOGGER_INVOICES** | ✅ Oui | ✅ Oui (plus détaillé) |
| **LOGGER_EMAIL** | ✅ Oui | ✅ Oui |
| **Logs Celery visibles** | ❌ Non/Limité | ✅ Oui (ultra-détaillé) |
| **Logs en temps réel** | ❌ Difficile | ✅ Oui (via Flower) |
| **Statistiques** | ❌ Non | ✅ Oui (vitesse, temps restant, etc.) |
| **Émojis pour lecture** | ❌ Non | ✅ Oui (✅❌📧⚡) |

---

## 🔧 Configuration recommandée

### 1. Activer les logs détaillés

Dans `/Users/paulo/SitesWeb/heron/heron/settings.py` :

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file_invoices': {
            'level': 'INFO',  # ou 'DEBUG' pour encore plus de détails
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/path/to/logs/invoices.log',
            'maxBytes': 1024 * 1024 * 50,  # 50MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'file_email': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/path/to/logs/email.log',
            'maxBytes': 1024 * 1024 * 50,
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'heron.loggers.LOGGER_INVOICES': {
            'handlers': ['file_invoices', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'heron.loggers.LOGGER_EMAIL': {
            'handlers': ['file_email', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        # Logger Celery
        'celery': {
            'handlers': ['file_invoices', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

### 2. Logs Celery dans un fichier dédié

Lors du lancement de Celery :

```bash
# Avec logs dans un fichier
celery -A heron worker --loglevel=info --logfile=/path/to/logs/celery.log

# Ou avec systemd
# Éditez /etc/systemd/system/celery.service
[Service]
ExecStart=/path/to/venv/bin/celery -A heron worker --loglevel=info --logfile=/var/log/celery/worker.log
```

### 3. Rotation automatique des logs

```bash
# Créez /etc/logrotate.d/heron
/path/to/logs/invoices.log
/path/to/logs/email.log
/path/to/logs/celery.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 www-data www-data
}
```

---

## 📈 Surveillance en production

### Script de monitoring

Créez `/usr/local/bin/monitor_email_sending.sh` :

```bash
#!/bin/bash

LOG_FILE="/path/to/logs/invoices.log"
TODAY=$(date +%Y-%m-%d)

echo "=== RAPPORT D'ENVOI DES EMAILS - $TODAY ==="
echo ""

# Nombre d'emails envoyés
SENT=$(grep "$TODAY" "$LOG_FILE" | grep -c "envoyé avec succès")
echo "✅ Emails envoyés: $SENT"

# Nombre d'erreurs
ERRORS=$(grep "$TODAY" "$LOG_FILE" | grep -c -i "error\|erreur")
echo "❌ Erreurs: $ERRORS"

# Taux de succès
if [ "$SENT" -gt 0 ]; then
    TOTAL=$((SENT + ERRORS))
    RATE=$(echo "scale=1; $SENT * 100 / $TOTAL" | bc)
    echo "📊 Taux de succès: ${RATE}%"
fi

echo ""
echo "=== DERNIÈRES ERREURS ==="
grep "$TODAY" "$LOG_FILE" | grep -i "error\|erreur" | tail -5

echo ""
echo "=== JOBS EN COURS ==="
# Requête à la base de données pour voir les jobs actifs
# (nécessite psql ou mysql selon votre DB)
```

Rendez-le exécutable :

```bash
chmod +x /usr/local/bin/monitor_email_sending.sh
```

Exécutez-le :

```bash
/usr/local/bin/monitor_email_sending.sh
```

### Tâche cron pour alertes

```bash
# Ajoutez dans crontab -e
# Vérifie toutes les 30 minutes et envoie un email si erreurs
*/30 * * * * /usr/local/bin/monitor_email_sending.sh | mail -s "Rapport envoi factures" admin@example.com
```

---

## 🐛 Dépannage

### Problème : Je ne vois pas les logs Celery

**Solution 1 : Vérifier le niveau de log**

```bash
# Relancez Celery avec --loglevel=debug
celery -A heron worker --loglevel=debug
```

**Solution 2 : Vérifier que la bonne tâche est utilisée**

Dans votre vue, vérifiez que vous utilisez bien :

```python
"celery_send_invoices_emails_gmail_enhanced"  # ← Version avec logs détaillés
```

et non :

```python
"celery_send_invoices_emails_gmail"  # ← Version basique
```

### Problème : Les traces ne s'enregistrent pas

**Solution : Vérifier les imports**

```python
# Dans votre tasks file
from apps.data_flux.trace import get_trace

# Vérifier que la fonction est bien appelée
trace = get_trace(...)
trace.save()  # ← Important!
```

### Problème : Flower ne se connecte pas

**Solution :**

```bash
# Vérifier que Celery utilise le bon broker
# Dans settings.py
CELERY_BROKER_URL = 'redis://localhost:6379/0'  # ou votre config

# Vérifier que Redis/RabbitMQ est en cours d'exécution
redis-cli ping  # devrait retourner PONG
```

---

## 📊 Dashboard personnalisé (bonus)

Créez une vue Django pour voir les stats en temps réel :

```python
# apps/invoices/views/dashboard_views.py
from django.shortcuts import render
from apps.data_flux.models import Trace
from apps.invoices.bin.api_gmail.models_progress import EmailSendProgress
from django.utils import timezone
from datetime import timedelta

def email_sending_dashboard(request):
    """Dashboard des envois d'emails"""
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)

    # Stats du jour
    traces_today = Trace.objects.filter(
        application_name="invoices_send_by_email_gmail",
        created_at__date=today
    )

    # Stats de la semaine
    traces_week = Trace.objects.filter(
        application_name="invoices_send_by_email_gmail",
        created_at__gte=week_ago
    )

    # Jobs en cours
    active_jobs = EmailSendProgress.objects.filter(
        status__in=["pending", "in_progress"]
    )

    # Jobs terminés aujourd'hui
    completed_jobs_today = EmailSendProgress.objects.filter(
        status="completed",
        completed_at__date=today
    )

    context = {
        "today_sent": traces_today.filter(errors=False).count(),
        "today_errors": traces_today.filter(errors=True).count(),
        "week_sent": traces_week.filter(errors=False).count(),
        "week_errors": traces_week.filter(errors=True).count(),
        "active_jobs": active_jobs,
        "completed_jobs_today": completed_jobs_today,
    }

    return render(request, "invoices/email_dashboard.html", context)
```

---

## 🎉 Résumé

Le nouveau système conserve **TOUS les logs de l'ancien** et en ajoute beaucoup plus :

✅ **Traces en DB** : Identiques à l'ancien (avec `get_trace()`)
✅ **Logs Python** : Plus détaillés qu'avant
✅ **Logs Celery** : Nouveaux, ultra-détaillés, visibles dans Flower
✅ **Statistiques** : Vitesse, temps restant, taux de succès
✅ **Monitoring temps réel** : Via Flower ou logs en direct

**Vous avez maintenant plus de visibilité que jamais sur vos envois d'emails ! 🚀📊**