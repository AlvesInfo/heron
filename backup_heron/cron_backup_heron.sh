#!/bin/bash
#===============================================================================
# Script wrapper pour exécution via cron
# Lancé automatiquement tous les jours à 3h00
#
# Installation:
#   1. Copier ce script: sudo cp cron_backup_heron.sh /usr/local/bin/
#   2. Rendre exécutable: sudo chmod +x /usr/local/bin/cron_backup_heron.sh
#   3. Installer le cron: sudo cp heron_backup.cron /etc/cron.d/heron_backup
#      OU utiliser: crontab -e
#===============================================================================

set -euo pipefail

#-------------------------------------------------------------------------------
# CONFIGURATION
#-------------------------------------------------------------------------------

# Chemin vers le script principal
BACKUP_SCRIPT="/opt/scripts/backup_restore_heron.sh"

# Utilisateur qui exécute le script (pour .pgpass)
BACKUP_USER="heron"

# Fichier de lock pour éviter les exécutions multiples
LOCK_FILE="/var/run/heron_backup.lock"

# Log spécifique au cron
CRON_LOG="/var/log/postgresql_backup/cron.log"

#-------------------------------------------------------------------------------
# FONCTIONS
#-------------------------------------------------------------------------------

log_cron() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "${CRON_LOG}"
}

cleanup() {
    rm -f "${LOCK_FILE}"
    log_cron "Lock libéré"
}

#-------------------------------------------------------------------------------
# VÉRIFICATIONS
#-------------------------------------------------------------------------------

# Créer le répertoire de log si nécessaire
mkdir -p "$(dirname "${CRON_LOG}")"

log_cron "=========================================="
log_cron "Démarrage du backup planifié"

# Vérifier que le script existe
if [[ ! -x "${BACKUP_SCRIPT}" ]]; then
    log_cron "ERREUR: Script non trouvé ou non exécutable: ${BACKUP_SCRIPT}"
    exit 1
fi

# Vérifier le lock (éviter exécutions simultanées)
if [[ -f "${LOCK_FILE}" ]]; then
    # Vérifier si le processus est toujours actif
    if kill -0 "$(cat "${LOCK_FILE}")" 2>/dev/null; then
        log_cron "ERREUR: Un backup est déjà en cours (PID: $(cat "${LOCK_FILE}"))"
        exit 1
    else
        log_cron "WARN: Lock orphelin trouvé, suppression..."
        rm -f "${LOCK_FILE}"
    fi
fi

# Créer le lock
echo $$ > "${LOCK_FILE}"
trap cleanup EXIT

#-------------------------------------------------------------------------------
# EXÉCUTION
#-------------------------------------------------------------------------------

log_cron "Lancement de ${BACKUP_SCRIPT} -y"

# Exécuter le script avec -y (sans confirmation)
# Rediriger stdout et stderr vers le log cron
if "${BACKUP_SCRIPT}" -y >> "${CRON_LOG}" 2>&1; then
    log_cron "Backup terminé avec SUCCÈS"
    exit 0
else
    exit_code=$?
    log_cron "Backup terminé avec ERREUR (code: ${exit_code})"
    exit ${exit_code}
fi
