# Guide d'installation - Backup automatique PostgreSQL

## Fichiers fournis

| Fichier | Description | Destination |
|---------|-------------|-------------|
| `backup_restore_heron.sh` | Script principal | `/opt/scripts/` |
| `cron_backup_heron.sh` | Wrapper pour cron | `/usr/local/bin/` |
| `heron_backup.cron` | Configuration cron | `/etc/cron.d/` |
| `credentials.conf.example` | Template credentials email | `/etc/heron_backup/` |

## Installation pas à pas

### 1. Créer les répertoires

```bash
sudo mkdir -p /opt/scripts
sudo mkdir -p /var/log/postgresql_backup
sudo mkdir -p /var/backups/postgresql
sudo mkdir -p /etc/heron_backup
```

### 2. Copier les scripts

```bash
# Script principal
sudo cp backup_restore_heron.sh /opt/scripts/
sudo chmod +x /opt/scripts/backup_restore_heron.sh

# Wrapper cron
sudo cp cron_backup_heron.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/cron_backup_heron.sh

# Configuration cron
sudo cp heron_backup.cron /etc/cron.d/heron_backup
sudo chmod 644 /etc/cron.d/heron_backup
```

### 3. Configurer l'authentification PostgreSQL

```bash
# Créer le fichier .pgpass pour l'utilisateur qui exécute le script
# (remplacer 'heron' par l'utilisateur système approprié)

sudo -u heron bash -c 'cat >> ~/.pgpass << EOF
10.9.2.109:5439:*:heron:MOT_DE_PASSE_POSTGRESQL
EOF'

sudo -u heron chmod 600 ~/.pgpass
```

### 4. Configurer les emails (optionnel)

```bash
# Copier le template
sudo cp credentials.conf.example /etc/heron_backup/credentials.conf

# Sécuriser
sudo chmod 600 /etc/heron_backup/credentials.conf
sudo chown heron:heron /etc/heron_backup/credentials.conf

# Éditer avec vos paramètres
sudo nano /etc/heron_backup/credentials.conf
```

### 5. Configurer les permissions

```bash
# Donner les droits à l'utilisateur heron
sudo chown -R heron:heron /var/log/postgresql_backup
sudo chown -R heron:heron /var/backups/postgresql
sudo chown heron:heron /opt/scripts/backup_restore_heron.sh
```

### 6. Adapter la configuration cron

Éditer `/etc/cron.d/heron_backup` et remplacer `heron` par le bon utilisateur système :

```bash
sudo nano /etc/cron.d/heron_backup
```

### 7. Tester

```bash
# Test en dry-run
sudo -u heron /opt/scripts/backup_restore_heron.sh --dry-run

# Test réel (avec confirmation)
sudo -u heron /opt/scripts/backup_restore_heron.sh

# Test du wrapper cron
sudo -u heron /usr/local/bin/cron_backup_heron.sh
```

### 8. Vérifier le cron

```bash
# Lister les crons actifs
sudo ls -la /etc/cron.d/

# Vérifier la syntaxe
cat /etc/cron.d/heron_backup

# Voir les logs cron système
sudo tail -f /var/log/syslog | grep -i cron
```

## Alternative : utiliser crontab personnel

Si vous préférez ne pas utiliser `/etc/cron.d/`, vous pouvez ajouter directement dans le crontab de l'utilisateur :

```bash
# Éditer le crontab de l'utilisateur heron
sudo -u heron crontab -e

# Ajouter cette ligne :
0 3 * * * /opt/scripts/backup_restore_heron.sh -y >> /var/log/postgresql_backup/cron.log 2>&1
```

## Vérification après installation

```bash
# Vérifier que le cron est bien installé
grep -r heron /etc/cron.d/

# Vérifier les permissions
ls -la /opt/scripts/backup_restore_heron.sh
ls -la /usr/local/bin/cron_backup_heron.sh
ls -la ~/.pgpass

# Vérifier les logs le lendemain
cat /var/log/postgresql_backup/cron.log
cat /var/log/postgresql_backup/heron_backup_restore.log
```

## Dépannage

### Le cron ne s'exécute pas

```bash
# Vérifier que cron est actif
sudo systemctl status cron

# Vérifier les logs
sudo grep CRON /var/log/syslog | tail -20

# Tester manuellement
sudo -u heron /usr/local/bin/cron_backup_heron.sh
```

### Erreur "Permission denied"

```bash
# Vérifier les permissions du script
ls -la /opt/scripts/backup_restore_heron.sh

# Corriger
sudo chmod +x /opt/scripts/backup_restore_heron.sh
```

### Erreur ".pgpass: permissions should be 600"

```bash
# Corriger les permissions
chmod 600 ~/.pgpass
```

### Erreur de connexion PostgreSQL

```bash
# Tester la connexion manuellement
psql -h 10.9.2.109 -p 5439 -U heron -d heron -c "SELECT 1;"

# Vérifier le contenu de .pgpass
cat ~/.pgpass
```

## Monitoring

### Surveiller les logs

```bash
# Logs en temps réel
tail -f /var/log/postgresql_backup/cron.log

# Dernière exécution
tail -50 /var/log/postgresql_backup/heron_backup_restore.log
```

### Vérifier l'état

```bash
/opt/scripts/backup_restore_heron.sh --status
```

## Désinstallation

```bash
# Supprimer le cron
sudo rm /etc/cron.d/heron_backup

# Supprimer les scripts (optionnel)
sudo rm /opt/scripts/backup_restore_heron.sh
sudo rm /usr/local/bin/cron_backup_heron.sh

# Conserver les logs et backups pour analyse si nécessaire
```
