#!/bin/bash
#===============================================================================
# Script de sauvegarde et restauration PostgreSQL
# Usage: ./backup_restore_heron.sh [OPTIONS]
#
# Options:
#   -d, --dry-run     Simuler l'exécution sans effectuer les opérations
#   -y, --yes         Ne pas demander de confirmation
#   -r, --rotate-only Effectuer uniquement la rotation des logs
#   -s, --status      Afficher l'état des logs et backups
#   -h, --help        Afficher l'aide
#
# Exemples:
#   ./backup_restore_heron.sh --dry-run    # Simuler
#   ./backup_restore_heron.sh -y           # Exécuter sans confirmation
#   ./backup_restore_heron.sh --rotate-only # Rotation des logs uniquement
#   ./backup_restore_heron.sh --status      # Voir l'état des fichiers
#   ./backup_restore_heron.sh              # Exécution normale avec confirmation
#===============================================================================

set -euo pipefail

#-------------------------------------------------------------------------------
# CONFIGURATION - À adapter selon ton environnement
#-------------------------------------------------------------------------------

# Serveur source (pour le dump)
SOURCE_HOST="10.9.2.109"
SOURCE_PORT="5439"
SOURCE_DB="heron"
SOURCE_USER="heron"

# Serveur destination (pour le restore)
# Mettre les mêmes valeurs si c'est le même serveur
DEST_HOST="10.9.2.109"
DEST_PORT="5439"
DEST_DB="heron_formation"
DEST_USER="heron"

# Répertoire de sauvegarde
BACKUP_DIR="/var/backups/postgresql"
BACKUP_RETENTION_DAYS=7           # Conserver les backups pendant X jours
BACKUP_FILE="${BACKUP_DIR}/heron_dump_$(date +%Y_%m_%d_%H%M%S).backup"
DELETE_DUMP_AFTER_RESTORE=true    # Supprimer le dump après restauration réussie

# Logging
LOG_DIR="/var/log/postgresql_backup"
LOG_FILE="${LOG_DIR}/heron_backup_restore.log"

# Configuration rotation des logs
LOG_MAX_SIZE_MB=10                # Taille max du log avant rotation (en Mo)
LOG_MAX_FILES=5                   # Nombre de fichiers de log à conserver
LOG_COMPRESS=true                 # Compresser les anciens logs (true/false)
LOG_ROTATE_ON_START=true          # Vérifier rotation au démarrage du script

# Configuration Email
# Les credentials sont stockés dans un fichier séparé pour la sécurité
# Voir: /etc/heron_backup/credentials.conf (chmod 600)
EMAIL_ENABLED=true
EMAIL_CREDENTIALS_FILE="/etc/heron_backup/credentials.conf"
EMAIL_SUBJECT_PREFIX="[PostgreSQL Backup]"
# Méthode d'envoi: "sendmail", "mailx", "msmtp" ou "curl" (pour API comme Mailgun/SendGrid)
EMAIL_METHOD="msmtp"

#-------------------------------------------------------------------------------
# VARIABLES GLOBALES
#-------------------------------------------------------------------------------

DRY_RUN=false
AUTO_YES=false
ROTATE_ONLY=false
SHOW_STATUS=false
SCRIPT_START_TIME=""
SCRIPT_END_TIME=""
ERRORS=()
WARNINGS=()

# Variables email (chargées depuis le fichier credentials)
EMAIL_TO=""
EMAIL_FROM=""
SMTP_HOST=""
SMTP_PORT=""
SMTP_USER=""
SMTP_PASSWORD=""
MAILGUN_API_KEY=""
MAILGUN_DOMAIN=""

#-------------------------------------------------------------------------------
# FONCTIONS - CREDENTIALS
#-------------------------------------------------------------------------------

load_email_credentials() {
    if [[ "${EMAIL_ENABLED}" != true ]]; then
        return 0
    fi
    
    if [[ ! -f "${EMAIL_CREDENTIALS_FILE}" ]]; then
        log_warn "Fichier credentials email non trouvé: ${EMAIL_CREDENTIALS_FILE}"
        log_warn "Notifications email désactivées"
        log_warn ""
        log_warn "Pour activer les emails, créer le fichier avec:"
        log_warn "  sudo mkdir -p /etc/heron_backup"
        log_warn "  sudo touch /etc/heron_backup/credentials.conf"
        log_warn "  sudo chmod 600 /etc/heron_backup/credentials.conf"
        log_warn "  sudo chown $(whoami) /etc/heron_backup/credentials.conf"
        EMAIL_ENABLED=false
        return 0
    fi
    
    # Vérifier les permissions (doit être 600 ou 400)
    local perms=$(stat -c "%a" "${EMAIL_CREDENTIALS_FILE}" 2>/dev/null || stat -f "%OLp" "${EMAIL_CREDENTIALS_FILE}" 2>/dev/null)
    if [[ "${perms}" != "600" ]] && [[ "${perms}" != "400" ]]; then
        log_error "Permissions incorrectes sur ${EMAIL_CREDENTIALS_FILE}: ${perms}"
        log_error "Le fichier doit avoir les permissions 600"
        log_error "Corriger avec: sudo chmod 600 ${EMAIL_CREDENTIALS_FILE}"
        EMAIL_ENABLED=false
        return 1
    fi
    
    # Charger les variables depuis le fichier
    # shellcheck source=/dev/null
    source "${EMAIL_CREDENTIALS_FILE}"
    
    # Vérifier les variables obligatoires
    if [[ -z "${EMAIL_TO}" ]] || [[ -z "${EMAIL_FROM}" ]]; then
        log_warn "EMAIL_TO ou EMAIL_FROM non définis dans ${EMAIL_CREDENTIALS_FILE}"
        EMAIL_ENABLED=false
        return 0
    fi
    
    log_info "Credentials email chargés depuis ${EMAIL_CREDENTIALS_FILE}"
}

#-------------------------------------------------------------------------------
# FONCTIONS - UTILITAIRES
#-------------------------------------------------------------------------------

show_help() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Script de sauvegarde et restauration PostgreSQL.
Sauvegarde '${SOURCE_DB}' et restaure vers '${DEST_DB}'.

Options:
    -d, --dry-run      Simuler l'exécution sans effectuer les opérations
    -y, --yes          Ne pas demander de confirmation
    -r, --rotate-only  Effectuer uniquement la rotation des logs
    -s, --status       Afficher l'état des logs et backups
    -h, --help         Afficher cette aide

Exemples:
    $(basename "$0") --dry-run     # Voir ce qui serait exécuté
    $(basename "$0") -y            # Exécuter sans confirmation
    $(basename "$0") --rotate-only # Rotation des logs uniquement
    $(basename "$0") --status      # État des fichiers
    $(basename "$0")               # Exécution normale

Configuration requise:

  1. PostgreSQL (.pgpass):
     echo '${SOURCE_HOST}:${SOURCE_PORT}:*:${SOURCE_USER}:MOT_DE_PASSE' >> ~/.pgpass
     chmod 600 ~/.pgpass

  2. Email (optionnel):
     sudo mkdir -p /etc/heron_backup
     sudo cp credentials.conf.example /etc/heron_backup/credentials.conf
     sudo chmod 600 /etc/heron_backup/credentials.conf
     # Éditer avec vos paramètres SMTP

Fichiers:
    Logs:         ${LOG_DIR}
    Backups:      ${BACKUP_DIR}
    Credentials:  ${EMAIL_CREDENTIALS_FILE}
    PostgreSQL:   ~/.pgpass

EOF
    exit 0
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -d|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -y|--yes)
                AUTO_YES=true
                shift
                ;;
            -r|--rotate-only)
                ROTATE_ONLY=true
                shift
                ;;
            -s|--status)
                SHOW_STATUS=true
                shift
                ;;
            -h|--help)
                show_help
                ;;
            *)
                echo "Option inconnue: $1"
                echo "Utiliser --help pour l'aide"
                exit 1
                ;;
        esac
    done
}

log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local prefix=""
    
    if [[ "${DRY_RUN}" == true ]]; then
        prefix="[DRY-RUN] "
    fi
    
    # Afficher à l'écran
    echo "[${timestamp}] [${level}] ${prefix}${message}"
    
    # Écrire dans le fichier log (si le répertoire existe)
    if [[ -d "${LOG_DIR}" ]]; then
        echo "[${timestamp}] [${level}] ${prefix}${message}" >> "${LOG_FILE}"
    fi
}

log_info() { log "INFO" "$1"; }
log_error() { log "ERROR" "$1"; ERRORS+=("$1"); }
log_warn() { log "WARN" "$1"; WARNINGS+=("$1"); }
log_success() { log "SUCCESS" "$1"; }

#-------------------------------------------------------------------------------
# FONCTIONS - ROTATION DES LOGS
#-------------------------------------------------------------------------------

get_file_size_mb() {
    local file="$1"
    if [[ -f "${file}" ]]; then
        # Compatible Linux et macOS
        local size_bytes
        if stat --version &>/dev/null 2>&1; then
            # GNU stat (Linux)
            size_bytes=$(stat -c%s "${file}" 2>/dev/null || echo "0")
        else
            # BSD stat (macOS)
            size_bytes=$(stat -f%z "${file}" 2>/dev/null || echo "0")
        fi
        echo $((size_bytes / 1024 / 1024))
    else
        echo "0"
    fi
}

rotate_logs() {
    local log_file="${1:-$LOG_FILE}"
    local max_size="${2:-$LOG_MAX_SIZE_MB}"
    local max_files="${3:-$LOG_MAX_FILES}"
    local compress="${4:-$LOG_COMPRESS}"
    
    # Vérifier si le fichier existe
    if [[ ! -f "${log_file}" ]]; then
        if [[ "${DRY_RUN}" == true ]]; then
            log_info "ROTATION: Fichier ${log_file} n'existe pas encore"
        fi
        return 0
    fi
    
    # Obtenir la taille actuelle
    local current_size=$(get_file_size_mb "${log_file}")
    
    log_info "Vérification rotation: ${log_file} (${current_size}Mo / ${max_size}Mo max)"
    
    # Vérifier si rotation nécessaire
    if [[ ${current_size} -lt ${max_size} ]]; then
        log_info "Pas de rotation nécessaire"
        return 0
    fi
    
    log_info "Rotation des logs nécessaire (${current_size}Mo >= ${max_size}Mo)..."
    
    if [[ "${DRY_RUN}" == true ]]; then
        log_info "SIMULERAIT: Rotation de ${log_file}"
        log_info "  - Décalage des fichiers .1 -> .2 -> ... -> .${max_files}"
        log_info "  - Suppression de ${log_file}.${max_files}*"
        if [[ "${compress}" == true ]]; then
            log_info "  - Compression en .gz"
        fi
        return 0
    fi
    
    # Supprimer le plus ancien si nécessaire
    local oldest="${log_file}.${max_files}"
    rm -f "${oldest}" "${oldest}.gz" 2>/dev/null || true
    
    # Décaler les fichiers existants (.4 -> .5, .3 -> .4, etc.)
    for ((i = max_files - 1; i >= 1; i--)); do
        local current="${log_file}.${i}"
        local next="${log_file}.$((i + 1))"
        
        if [[ -f "${current}" ]]; then
            mv "${current}" "${next}"
        fi
        if [[ -f "${current}.gz" ]]; then
            mv "${current}.gz" "${next}.gz"
        fi
    done
    
    # Déplacer le log actuel vers .1
    mv "${log_file}" "${log_file}.1"
    
    # Compresser si demandé (en arrière-plan pour ne pas bloquer)
    if [[ "${compress}" == true ]] && command -v gzip &> /dev/null; then
        gzip -f "${log_file}.1" &
        log_info "Compression de ${log_file}.1 en cours..."
    fi
    
    # Créer un nouveau fichier log vide
    touch "${log_file}"
    
    log_success "Rotation effectuée: ${log_file} -> ${log_file}.1"
}

cleanup_old_logs() {
    local log_file="${1:-$LOG_FILE}"
    local max_files="${2:-$LOG_MAX_FILES}"
    
    log_info "Nettoyage des anciens logs (> ${max_files} fichiers)..."
    
    local log_dir=$(dirname "${log_file}")
    local log_name=$(basename "${log_file}")
    local deleted_count=0
    
    # Supprimer les fichiers au-delà de max_files
    for f in "${log_dir}/${log_name}."*; do
        if [[ -f "${f}" ]]; then
            # Extraire le numéro du fichier
            local num=$(echo "${f}" | grep -oE '\.[0-9]+' | tail -1 | tr -d '.' || echo "")
            if [[ -n "${num}" ]] && [[ ${num} -gt ${max_files} ]]; then
                if [[ "${DRY_RUN}" == true ]]; then
                    log_info "SIMULERAIT suppression: ${f}"
                else
                    rm -f "${f}"
                    log_info "Supprimé: ${f}"
                fi
                ((deleted_count++))
            fi
        fi
    done
    
    if [[ ${deleted_count} -eq 0 ]]; then
        log_info "Aucun ancien log à supprimer"
    else
        log_success "Nettoyage terminé: ${deleted_count} fichier(s) supprimé(s)"
    fi
}

show_status() {
    echo ""
    echo "==============================================================================="
    echo "                    ÉTAT DES FICHIERS - PostgreSQL Backup"
    echo "==============================================================================="
    
    # Section Logs
    echo ""
    echo "📋 LOGS"
    echo "--------------------------------------------------------------------------------"
    echo "Répertoire:     ${LOG_DIR}"
    echo "Fichier actuel: ${LOG_FILE}"
    echo ""
    echo "Configuration rotation:"
    echo "  - Taille max:        ${LOG_MAX_SIZE_MB} Mo"
    echo "  - Fichiers conservés: ${LOG_MAX_FILES}"
    echo "  - Compression:       ${LOG_COMPRESS}"
    echo "  - Rotation auto:     ${LOG_ROTATE_ON_START}"
    echo ""
    
    if [[ -d "${LOG_DIR}" ]]; then
        echo "Fichiers présents:"
        echo ""
        printf "  %-50s %10s %s\n" "FICHIER" "TAILLE" "DATE"
        echo "  $(printf '%.0s-' {1..75})"
        
        for f in "${LOG_FILE}" "${LOG_FILE}."*; do
            if [[ -f "${f}" ]]; then
                local size=$(du -h "${f}" 2>/dev/null | cut -f1)
                local date=$(date -r "${f}" '+%Y-%m-%d %H:%M' 2>/dev/null || stat -c '%y' "${f}" 2>/dev/null | cut -d'.' -f1)
                local name=$(basename "${f}")
                printf "  %-50s %10s %s\n" "${name}" "${size}" "${date}"
            fi
        done 2>/dev/null || true
        
        echo ""
        local total_log_size=$(du -sh "${LOG_DIR}" 2>/dev/null | cut -f1)
        echo "  Taille totale logs: ${total_log_size}"
    else
        echo "  ⚠️  Répertoire de logs non créé"
    fi
    
    # Section Backups
    echo ""
    echo "💾 BACKUPS"
    echo "--------------------------------------------------------------------------------"
    echo "Répertoire: ${BACKUP_DIR}"
    echo "Rétention:  ${BACKUP_RETENTION_DAYS} jours"
    echo ""
    
    if [[ -d "${BACKUP_DIR}" ]]; then
        local backup_count=$(find "${BACKUP_DIR}" -name "heron_dump_*.backup" 2>/dev/null | wc -l)
        echo "Fichiers présents: ${backup_count}"
        echo ""
        
        if [[ ${backup_count} -gt 0 ]]; then
            printf "  %-45s %10s %s\n" "FICHIER" "TAILLE" "DATE"
            echo "  $(printf '%.0s-' {1..70})"
            
            find "${BACKUP_DIR}" -name "heron_dump_*.backup" -printf "%T@ %p\n" 2>/dev/null | \
            sort -rn | head -10 | while read -r timestamp filepath; do
                local size=$(du -h "${filepath}" 2>/dev/null | cut -f1)
                local date=$(date -d "@${timestamp%%.*}" '+%Y-%m-%d %H:%M' 2>/dev/null || date -r "${timestamp%%.*}" '+%Y-%m-%d %H:%M' 2>/dev/null)
                local name=$(basename "${filepath}")
                printf "  %-45s %10s %s\n" "${name}" "${size}" "${date}"
            done 2>/dev/null || \
            ls -lht "${BACKUP_DIR}"/heron_dump_*.backup 2>/dev/null | head -10 | while read -r line; do
                echo "  ${line}"
            done
            
            if [[ ${backup_count} -gt 10 ]]; then
                echo "  ... et $((backup_count - 10)) autres fichiers"
            fi
        fi
        
        echo ""
        local total_backup_size=$(du -sh "${BACKUP_DIR}" 2>/dev/null | cut -f1)
        echo "  Taille totale backups: ${total_backup_size}"
        
        # Fichiers qui seront supprimés au prochain nettoyage
        local old_count=$(find "${BACKUP_DIR}" -name "heron_dump_*.backup" -mtime +${BACKUP_RETENTION_DAYS} 2>/dev/null | wc -l)
        if [[ ${old_count} -gt 0 ]]; then
            echo ""
            echo "  ⚠️  ${old_count} fichier(s) de plus de ${BACKUP_RETENTION_DAYS} jours (sera supprimé au prochain run)"
        fi
    else
        echo "  ⚠️  Répertoire de backups non créé"
    fi
    
    # Section Espace disque
    echo ""
    echo "💿 ESPACE DISQUE"
    echo "--------------------------------------------------------------------------------"
    df -h "${BACKUP_DIR}" 2>/dev/null | tail -1 | awk '{printf "  Partition: %s\n  Utilisé: %s / %s (%s)\n  Disponible: %s\n", $1, $3, $2, $5, $4}'
    
    echo ""
    echo "==============================================================================="
    echo ""
}

#-------------------------------------------------------------------------------
# FONCTIONS - EMAIL
#-------------------------------------------------------------------------------

send_email() {
    local subject="$1"
    local body="$2"
    local status="$3"
    
    if [[ "${EMAIL_ENABLED}" != true ]]; then
        log_info "Notification email désactivée"
        return 0
    fi
    
    if [[ "${DRY_RUN}" == true ]]; then
        log_info "SIMULERAIT: Envoi email à ${EMAIL_TO}"
        log_info "  Sujet: ${EMAIL_SUBJECT_PREFIX} ${subject}"
        return 0
    fi
    
    local full_subject="${EMAIL_SUBJECT_PREFIX} ${subject}"
    
    log_info "Envoi de la notification email à ${EMAIL_TO}..."
    
    case "${EMAIL_METHOD}" in
        sendmail)
            send_email_sendmail "${full_subject}" "${body}"
            ;;
        mailx)
            send_email_mailx "${full_subject}" "${body}"
            ;;
        msmtp)
            send_email_msmtp "${full_subject}" "${body}"
            ;;
        curl)
            send_email_curl "${full_subject}" "${body}"
            ;;
        *)
            log_warn "Méthode email '${EMAIL_METHOD}' non supportée"
            return 1
            ;;
    esac
}

send_email_sendmail() {
    local subject="$1"
    local body="$2"
    
    if ! command -v sendmail &> /dev/null; then
        log_warn "sendmail n'est pas installé"
        return 1
    fi
    
    {
        echo "From: ${EMAIL_FROM}"
        echo "To: ${EMAIL_TO}"
        echo "Subject: ${subject}"
        echo "Content-Type: text/plain; charset=utf-8"
        echo ""
        echo "${body}"
    } | sendmail -t
    
    log_success "Email envoyé via sendmail"
}

send_email_mailx() {
    local subject="$1"
    local body="$2"
    
    if ! command -v mailx &> /dev/null && ! command -v mail &> /dev/null; then
        log_warn "mailx/mail n'est pas installé"
        return 1
    fi
    
    echo "${body}" | mailx -s "${subject}" -r "${EMAIL_FROM}" "${EMAIL_TO}"
    
    log_success "Email envoyé via mailx"
}

send_email_msmtp() {
    local subject="$1"
    local body="$2"
    
    if ! command -v msmtp &> /dev/null; then
        log_warn "msmtp n'est pas installé (sudo apt install msmtp)"
        return 1
    fi
    
    # Si SMTP configuré dans credentials.conf, utiliser ces paramètres
    if [[ -n "${SMTP_HOST}" ]] && [[ -n "${SMTP_USER}" ]] && [[ -n "${SMTP_PASSWORD}" ]]; then
        {
            echo "From: ${EMAIL_FROM}"
            echo "To: ${EMAIL_TO}"
            echo "Subject: ${subject}"
            echo "Content-Type: text/plain; charset=utf-8"
            echo ""
            echo "${body}"
        } | msmtp \
            --host="${SMTP_HOST}" \
            --port="${SMTP_PORT:-587}" \
            --auth=on \
            --user="${SMTP_USER}" \
            --passwordeval="echo '${SMTP_PASSWORD}'" \
            --tls=on \
            --from="${EMAIL_FROM}" \
            "${EMAIL_TO}"
    else
        # Sinon utiliser ~/.msmtprc
        if [[ ! -f ~/.msmtprc ]]; then
            log_warn "Ni SMTP_* dans credentials.conf ni ~/.msmtprc trouvé"
            return 1
        fi
        
        {
            echo "From: ${EMAIL_FROM}"
            echo "To: ${EMAIL_TO}"
            echo "Subject: ${subject}"
            echo "Content-Type: text/plain; charset=utf-8"
            echo ""
            echo "${body}"
        } | msmtp "${EMAIL_TO}"
    fi
    
    log_success "Email envoyé via msmtp"
}

send_email_curl() {
    local subject="$1"
    local body="$2"
    
    if [[ -z "${MAILGUN_API_KEY}" ]] || [[ -z "${MAILGUN_DOMAIN}" ]]; then
        log_warn "MAILGUN_API_KEY ou MAILGUN_DOMAIN non définis dans ${EMAIL_CREDENTIALS_FILE}"
        return 1
    fi
    
    curl -s --user "api:${MAILGUN_API_KEY}" \
        "https://api.mailgun.net/v3/${MAILGUN_DOMAIN}/messages" \
        -F from="${EMAIL_FROM}" \
        -F to="${EMAIL_TO}" \
        -F subject="${subject}" \
        -F text="${body}"
    
    log_success "Email envoyé via Mailgun API"
}

build_email_body() {
    local status="$1"
    local duration="$2"
    local backup_size="${3:-N/A}"
    
    cat << EOF
================================================================================
RAPPORT DE SAUVEGARDE/RESTAURATION PostgreSQL
================================================================================

Statut: ${status}
Date d'exécution: $(date '+%Y-%m-%d %H:%M:%S')
Durée: ${duration}
Serveur: $(hostname)

--------------------------------------------------------------------------------
CONFIGURATION
--------------------------------------------------------------------------------

Source:
  - Hôte: ${SOURCE_HOST}:${SOURCE_PORT}
  - Base: ${SOURCE_DB}
  - Utilisateur: ${SOURCE_USER}

Destination:
  - Hôte: ${DEST_HOST}:${DEST_PORT}
  - Base: ${DEST_DB}
  - Utilisateur: ${DEST_USER}

Fichier de backup: ${BACKUP_FILE}
Taille du backup: ${backup_size}

--------------------------------------------------------------------------------
RÉSUMÉ DES OPÉRATIONS
--------------------------------------------------------------------------------

1. Dump de la base source: $(if [[ "${status}" == "SUCCESS" ]] || [[ "${status}" == "PARTIAL" ]]; then echo "OK"; else echo "ÉCHEC"; fi)
2. Suppression de la base destination: $(if [[ "${status}" == "SUCCESS" ]] || [[ "${status}" == "PARTIAL" ]]; then echo "OK"; else echo "ÉCHEC"; fi)
3. Création de la nouvelle base: $(if [[ "${status}" == "SUCCESS" ]] || [[ "${status}" == "PARTIAL" ]]; then echo "OK"; else echo "ÉCHEC"; fi)
4. Restauration des données: $(if [[ "${status}" == "SUCCESS" ]]; then echo "OK"; else echo "ÉCHEC ou WARNINGS"; fi)
5. Suppression du fichier dump: $(if [[ "${DELETE_DUMP_AFTER_RESTORE}" == true ]]; then echo "OK"; else echo "CONSERVÉ"; fi)

EOF

    if [[ ${#ERRORS[@]} -gt 0 ]]; then
        echo "--------------------------------------------------------------------------------"
        echo "ERREURS (${#ERRORS[@]})"
        echo "--------------------------------------------------------------------------------"
        for error in "${ERRORS[@]}"; do
            echo "  ❌ ${error}"
        done
        echo ""
    fi

    if [[ ${#WARNINGS[@]} -gt 0 ]]; then
        echo "--------------------------------------------------------------------------------"
        echo "AVERTISSEMENTS (${#WARNINGS[@]})"
        echo "--------------------------------------------------------------------------------"
        for warning in "${WARNINGS[@]}"; do
            echo "  ⚠️  ${warning}"
        done
        echo ""
    fi

    cat << EOF
--------------------------------------------------------------------------------
FICHIERS
--------------------------------------------------------------------------------

Log complet: ${LOG_FILE}
Backup: ${BACKUP_FILE}

================================================================================
Ce message a été généré automatiquement par le script de backup PostgreSQL.
================================================================================
EOF
}

#-------------------------------------------------------------------------------
# FONCTIONS - OPÉRATIONS PRINCIPALES
#-------------------------------------------------------------------------------

check_prerequisites() {
    log_info "Vérification des prérequis..."
    
    local missing_tools=()
    
    for tool in pg_dump pg_restore psql; do
        if ! command -v "${tool}" &> /dev/null; then
            missing_tools+=("${tool}")
        fi
    done
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        log_error "Outils manquants: ${missing_tools[*]}"
        log_error "Installer avec: sudo apt install postgresql-client"
        exit 1
    fi
    
    # Créer le répertoire de backup si nécessaire
    if [[ ! -d "${BACKUP_DIR}" ]]; then
        if [[ "${DRY_RUN}" == true ]]; then
            log_info "SIMULERAIT: Création du répertoire ${BACKUP_DIR}"
        else
            log_info "Création du répertoire de backup: ${BACKUP_DIR}"
            mkdir -p "${BACKUP_DIR}"
        fi
    fi
    
    # Créer le répertoire de log si nécessaire
    if [[ ! -d "${LOG_DIR}" ]]; then
        if [[ "${DRY_RUN}" == true ]]; then
            log_info "SIMULERAIT: Création du répertoire ${LOG_DIR}"
        else
            mkdir -p "${LOG_DIR}"
            log_info "Répertoire de logs créé: ${LOG_DIR}"
        fi
    fi
    
    log_success "Prérequis OK"
}

check_password() {
    local pgpass_file="${HOME}/.pgpass"
    
    if [[ ! -f "${pgpass_file}" ]]; then
        log_error "Fichier .pgpass non trouvé: ${pgpass_file}"
        log_error ""
        log_error "Créer le fichier avec:"
        log_error "  echo '${SOURCE_HOST}:${SOURCE_PORT}:*:${SOURCE_USER}:MOT_DE_PASSE' >> ~/.pgpass"
        log_error "  chmod 600 ~/.pgpass"
        exit 1
    fi
    
    # Vérifier les permissions (doit être 600)
    local perms=$(stat -c "%a" "${pgpass_file}" 2>/dev/null || stat -f "%OLp" "${pgpass_file}" 2>/dev/null)
    if [[ "${perms}" != "600" ]]; then
        log_error "Permissions incorrectes sur ${pgpass_file}: ${perms} (attendu: 600)"
        log_error "Corriger avec: chmod 600 ~/.pgpass"
        exit 1
    fi
    
    # Vérifier que les entrées existent pour nos serveurs
    if ! grep -q "^${SOURCE_HOST}:${SOURCE_PORT}:" "${pgpass_file}" && \
       ! grep -q "^${SOURCE_HOST}:\*:" "${pgpass_file}" && \
       ! grep -q "^\*:${SOURCE_PORT}:" "${pgpass_file}" && \
       ! grep -q "^\*:\*:" "${pgpass_file}"; then
        log_warn "Aucune entrée trouvée dans .pgpass pour ${SOURCE_HOST}:${SOURCE_PORT}"
        log_warn "Ajouter: ${SOURCE_HOST}:${SOURCE_PORT}:*:${SOURCE_USER}:MOT_DE_PASSE"
    fi
    
    log_success "Authentification .pgpass configurée"
}

test_connections() {
    log_info "Test des connexions aux serveurs PostgreSQL..."
    
    if [[ "${DRY_RUN}" == true ]]; then
        log_info "SIMULERAIT: Test de connexion à ${SOURCE_HOST}:${SOURCE_PORT}"
        log_info "SIMULERAIT: Test de connexion à ${DEST_HOST}:${DEST_PORT}"
        return 0
    fi
    
    if ! psql -h "${SOURCE_HOST}" -p "${SOURCE_PORT}" -U "${SOURCE_USER}" -d "${SOURCE_DB}" --no-password -c "SELECT 1;" &> /dev/null; then
        log_error "Impossible de se connecter à la base source ${SOURCE_DB}@${SOURCE_HOST}:${SOURCE_PORT}"
        exit 1
    fi
    log_success "Connexion source OK"
    
    if ! psql -h "${DEST_HOST}" -p "${DEST_PORT}" -U "${DEST_USER}" -d "postgres" --no-password -c "SELECT 1;" &> /dev/null; then
        log_error "Impossible de se connecter au serveur destination ${DEST_HOST}:${DEST_PORT}"
        exit 1
    fi
    log_success "Connexion destination OK"
}

do_backup() {
    log_info "Démarrage du dump de ${SOURCE_DB}@${SOURCE_HOST}:${SOURCE_PORT}..."
    log_info "Fichier de destination: ${BACKUP_FILE}"
    
    if [[ "${DRY_RUN}" == true ]]; then
        log_info "SIMULERAIT: pg_dump -h ${SOURCE_HOST} -p ${SOURCE_PORT} -U ${SOURCE_USER} -d ${SOURCE_DB} -Fc -f ${BACKUP_FILE} --verbose --no-password"
        return 0
    fi
    
    # Compter le nombre de tables pour la progression
    local total_tables=$(psql \
        -h "${SOURCE_HOST}" \
        -p "${SOURCE_PORT}" \
        -U "${SOURCE_USER}" \
        -d "${SOURCE_DB}" \
        --no-password \
        -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';" 2>/dev/null || echo "0")
    
    log_info "Tables à sauvegarder: ${total_tables}"
    
    local start_time=$(date +%s)
    local temp_counter=$(mktemp)
    echo "0" > "${temp_counter}"
    
    # Exécuter pg_dump et parser la sortie pour la progression
    pg_dump \
        -h "${SOURCE_HOST}" \
        -p "${SOURCE_PORT}" \
        -U "${SOURCE_USER}" \
        -d "${SOURCE_DB}" \
        -Fc \
        -f "${BACKUP_FILE}" \
        --verbose \
        --no-password 2>&1 | while IFS= read -r line; do
        
        # Logger dans le fichier
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ${line}" >> "${LOG_FILE}"
        
        # Détecter le dump d'une table
        if [[ "${line}" == *"dumping contents of table"* ]]; then
            local current_table=$(($(cat "${temp_counter}") + 1))
            echo "${current_table}" > "${temp_counter}"
            
            local table_name=$(echo "${line}" | sed 's/.*table "\([^"]*\)".*/\1/' | sed 's/.*table \(.*\)/\1/')
            
            if [[ ${total_tables} -gt 0 ]]; then
                local percent=$((current_table * 100 / total_tables))
                local bar_width=40
                local filled=$((percent * bar_width / 100))
                local empty=$((bar_width - filled))
                local bar=$(printf "%${filled}s" | tr ' ' '█')$(printf "%${empty}s" | tr ' ' '░')
                
                printf "\r  [${bar}] %3d%% (%d/%d) %-40s" "${percent}" "${current_table}" "${total_tables}" "${table_name:0:40}"
            else
                printf "\r  Table %d: %-50s" "${current_table}" "${table_name:0:50}"
            fi
        fi
    done
    
    local exit_code=${PIPESTATUS[0]}
    local final_count=$(cat "${temp_counter}")
    rm -f "${temp_counter}"
    
    # Nouvelle ligne après la barre de progression
    echo ""
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    if [[ ${exit_code} -eq 0 ]] && [[ -f "${BACKUP_FILE}" ]]; then
        local size=$(du -h "${BACKUP_FILE}" | cut -f1)
        log_success "Dump terminé: ${final_count} tables en ${duration}s (${size})"
        echo "${size}"
    else
        log_error "Échec du dump"
        return 1
    fi
}

drop_database() {
    log_info "Vérification de l'existence de la base ${DEST_DB}..."
    
    if [[ "${DRY_RUN}" == true ]]; then
        log_info "SIMULERAIT: Vérification existence de ${DEST_DB}"
        log_info "SIMULERAIT: Terminaison des connexions actives sur ${DEST_DB}"
        log_info "SIMULERAIT: DROP DATABASE IF EXISTS ${DEST_DB}"
        return 0
    fi
    
    local db_exists=$(psql \
        -h "${DEST_HOST}" \
        -p "${DEST_PORT}" \
        -U "${DEST_USER}" \
        -d "postgres" \
        -tAc "SELECT 1 FROM pg_database WHERE datname='${DEST_DB}'" \
        --no-password 2>/dev/null || echo "")
    
    if [[ "${db_exists}" == "1" ]]; then
        log_info "Suppression de la base ${DEST_DB}..."
        
        psql \
            -h "${DEST_HOST}" \
            -p "${DEST_PORT}" \
            -U "${DEST_USER}" \
            -d "postgres" \
            --no-password \
            -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${DEST_DB}' AND pid <> pg_backend_pid();" \
            2>&1 | tee -a "${LOG_FILE}"
        
        if psql \
            -h "${DEST_HOST}" \
            -p "${DEST_PORT}" \
            -U "${DEST_USER}" \
            -d "postgres" \
            --no-password \
            -c "DROP DATABASE IF EXISTS ${DEST_DB};" 2>&1 | tee -a "${LOG_FILE}"; then
            log_success "Base ${DEST_DB} supprimée"
        else
            log_error "Échec de la suppression de ${DEST_DB}"
            return 1
        fi
    else
        log_info "La base ${DEST_DB} n'existe pas, pas de suppression nécessaire"
    fi
}

create_database() {
    log_info "Création de la base ${DEST_DB}..."
    
    if [[ "${DRY_RUN}" == true ]]; then
        log_info "SIMULERAIT: CREATE DATABASE ${DEST_DB} WITH OWNER = ${DEST_USER} ENCODING = 'UTF8' LC_COLLATE = 'fr_FR.UTF-8' LC_CTYPE = 'fr_FR.UTF-8' TEMPLATE = template0"
        return 0
    fi
    
    if psql \
        -h "${DEST_HOST}" \
        -p "${DEST_PORT}" \
        -U "${DEST_USER}" \
        -d "postgres" \
        --no-password \
        -c "CREATE DATABASE ${DEST_DB} WITH OWNER = ${DEST_USER} ENCODING = 'UTF8' LC_COLLATE = 'fr_FR.UTF-8' LC_CTYPE = 'fr_FR.UTF-8' TEMPLATE = template0;" 2>&1 | tee -a "${LOG_FILE}"; then
        log_success "Base ${DEST_DB} créée"
    else
        log_error "Échec de la création de ${DEST_DB}"
        return 1
    fi
}

do_restore() {
    log_info "Restauration du dump vers ${DEST_DB}@${DEST_HOST}:${DEST_PORT}..."
    
    if [[ "${DRY_RUN}" == true ]]; then
        log_info "SIMULERAIT: pg_restore -h ${DEST_HOST} -p ${DEST_PORT} -U ${DEST_USER} -d ${DEST_DB} --verbose --no-password --no-owner --no-privileges ${BACKUP_FILE}"
        return 0
    fi
    
    # Compter le nombre d'objets dans le dump pour la progression
    local total_objects=$(pg_restore --list "${BACKUP_FILE}" 2>/dev/null | grep -v "^;" | grep -v "^$" | wc -l || echo "0")
    
    log_info "Objets à restaurer: ${total_objects}"
    
    local start_time=$(date +%s)
    
    # Fichiers temporaires pour les compteurs (car la boucle while est dans un sous-shell)
    local temp_dir=$(mktemp -d)
    echo "0" > "${temp_dir}/objects"
    echo "0" > "${temp_dir}/tables"
    echo "0" > "${temp_dir}/data"
    echo "0" > "${temp_dir}/indexes"
    echo "0" > "${temp_dir}/constraints"
    
    # Exécuter pg_restore et parser la sortie pour la progression
    pg_restore \
        -h "${DEST_HOST}" \
        -p "${DEST_PORT}" \
        -U "${DEST_USER}" \
        -d "${DEST_DB}" \
        --verbose \
        --no-password \
        --no-owner \
        --no-privileges \
        "${BACKUP_FILE}" 2>&1 | while IFS= read -r line; do
        
        # Logger dans le fichier
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ${line}" >> "${LOG_FILE}"
        
        # Détecter les différents types d'objets
        local object_type=""
        local object_name=""
        local current_object=$(cat "${temp_dir}/objects")
        
        if [[ "${line}" == *"creating TABLE"* ]]; then
            echo "$(($(cat "${temp_dir}/tables") + 1))" > "${temp_dir}/tables"
            current_object=$((current_object + 1))
            echo "${current_object}" > "${temp_dir}/objects"
            object_type="TABLE"
            object_name=$(echo "${line}" | sed 's/.*creating TABLE "\([^"]*\)".*/\1/' | sed 's/.*TABLE //')
        elif [[ "${line}" == *"processing data for table"* ]]; then
            echo "$(($(cat "${temp_dir}/data") + 1))" > "${temp_dir}/data"
            current_object=$((current_object + 1))
            echo "${current_object}" > "${temp_dir}/objects"
            object_type="DATA"
            object_name=$(echo "${line}" | sed 's/.*table "\([^"]*\)".*/\1/')
        elif [[ "${line}" == *"creating INDEX"* ]]; then
            echo "$(($(cat "${temp_dir}/indexes") + 1))" > "${temp_dir}/indexes"
            current_object=$((current_object + 1))
            echo "${current_object}" > "${temp_dir}/objects"
            object_type="INDEX"
            object_name=$(echo "${line}" | sed 's/.*creating INDEX "\([^"]*\)".*/\1/' | sed 's/.*INDEX //')
        elif [[ "${line}" == *"creating CONSTRAINT"* ]] || [[ "${line}" == *"creating FK CONSTRAINT"* ]]; then
            echo "$(($(cat "${temp_dir}/constraints") + 1))" > "${temp_dir}/constraints"
            current_object=$((current_object + 1))
            echo "${current_object}" > "${temp_dir}/objects"
            object_type="CONSTRAINT"
            object_name=$(echo "${line}" | sed 's/.*CONSTRAINT "\([^"]*\)".*/\1/' | sed 's/.*CONSTRAINT //')
        elif [[ "${line}" == *"creating"* ]] && [[ "${line}" != *"creating SCHEMA"* ]]; then
            current_object=$((current_object + 1))
            echo "${current_object}" > "${temp_dir}/objects"
            object_type="OBJECT"
            object_name=$(echo "${line}" | sed 's/pg_restore: //' | cut -c1-40)
        fi
        
        # Afficher la progression
        if [[ -n "${object_type}" ]]; then
            if [[ ${total_objects} -gt 0 ]]; then
                local percent=$((current_object * 100 / total_objects))
                [[ ${percent} -gt 100 ]] && percent=100
                
                local bar_width=40
                local filled=$((percent * bar_width / 100))
                local empty=$((bar_width - filled))
                local bar=$(printf "%${filled}s" | tr ' ' '█')$(printf "%${empty}s" | tr ' ' '░')
                
                printf "\r  [${bar}] %3d%% %-12s %-35s" "${percent}" "${object_type}" "${object_name:0:35}"
            else
                printf "\r  %-12s %-50s" "${object_type}" "${object_name:0:50}"
            fi
        fi
    done
    
    local exit_code=${PIPESTATUS[0]}
    
    # Récupérer les compteurs finaux
    local final_tables=$(cat "${temp_dir}/tables")
    local final_data=$(cat "${temp_dir}/data")
    local final_indexes=$(cat "${temp_dir}/indexes")
    local final_constraints=$(cat "${temp_dir}/constraints")
    rm -rf "${temp_dir}"
    
    # Nouvelle ligne après la barre de progression
    echo ""
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    # Afficher le résumé
    echo ""
    echo "  ┌─────────────────────────────────────┐"
    echo "  │       RÉSUMÉ DE RESTAURATION        │"
    echo "  ├─────────────────────────────────────┤"
    printf "  │  Tables créées:     %6d          │\n" "${final_tables}"
    printf "  │  Données chargées:  %6d tables   │\n" "${final_data}"
    printf "  │  Index créés:       %6d          │\n" "${final_indexes}"
    printf "  │  Contraintes:       %6d          │\n" "${final_constraints}"
    echo "  ├─────────────────────────────────────┤"
    printf "  │  Durée totale:      %6ds         │\n" "${duration}"
    echo "  └─────────────────────────────────────┘"
    echo ""
    
    if [[ ${exit_code} -eq 0 ]]; then
        log_success "Restauration terminée avec succès"
    else
        log_warn "Restauration terminée avec des warnings (vérifier le log)"
    fi
}

cleanup_old_backups() {
    log_info "Nettoyage des anciens backups (> ${BACKUP_RETENTION_DAYS} jours)..."
    
    if [[ "${DRY_RUN}" == true ]]; then
        log_info "SIMULERAIT: find ${BACKUP_DIR} -name 'heron_dump_*.backup' -mtime +${BACKUP_RETENTION_DAYS} -delete"
        local old_files=$(find "${BACKUP_DIR}" -name "heron_dump_*.backup" -mtime +${BACKUP_RETENTION_DAYS} 2>/dev/null || true)
        if [[ -n "${old_files}" ]]; then
            log_info "Fichiers qui seraient supprimés:"
            echo "${old_files}" | while read -r f; do log_info "  - ${f}"; done
        else
            log_info "Aucun backup à supprimer"
        fi
        return 0
    fi
    
    local count=$(find "${BACKUP_DIR}" -name "heron_dump_*.backup" -mtime +${BACKUP_RETENTION_DAYS} 2>/dev/null | wc -l)
    find "${BACKUP_DIR}" -name "heron_dump_*.backup" -mtime +${BACKUP_RETENTION_DAYS} -delete 2>/dev/null || true
    
    if [[ ${count} -gt 0 ]]; then
        log_success "Nettoyage terminé: ${count} fichier(s) supprimé(s)"
    else
        log_info "Aucun backup à supprimer"
    fi
}

delete_dump_file() {
    if [[ "${DELETE_DUMP_AFTER_RESTORE}" != true ]]; then
        log_info "Conservation du fichier dump (DELETE_DUMP_AFTER_RESTORE=false)"
        return 0
    fi
    
    log_info "Suppression du fichier dump: ${BACKUP_FILE}..."
    
    if [[ "${DRY_RUN}" == true ]]; then
        log_info "SIMULERAIT: rm -f ${BACKUP_FILE}"
        return 0
    fi
    
    if [[ -f "${BACKUP_FILE}" ]]; then
        rm -f "${BACKUP_FILE}"
        log_success "Fichier dump supprimé: ${BACKUP_FILE}"
    else
        log_warn "Fichier dump introuvable: ${BACKUP_FILE}"
    fi
}

show_summary() {
    echo ""
    echo "==============================================================================="
    echo "                              RÉSUMÉ"
    echo "==============================================================================="
    if [[ "${DRY_RUN}" == true ]]; then
        echo "Mode:        DRY-RUN (aucune opération effectuée)"
    fi
    echo "Source:      ${SOURCE_DB}@${SOURCE_HOST}:${SOURCE_PORT}"
    echo "Destination: ${DEST_DB}@${DEST_HOST}:${DEST_PORT}"
    if [[ "${DELETE_DUMP_AFTER_RESTORE}" == true ]]; then
        echo "Backup:      ${BACKUP_FILE} (supprimé après restore)"
    else
        echo "Backup:      ${BACKUP_FILE}"
    fi
    echo "Log:         ${LOG_FILE}"
    echo "==============================================================================="
    echo ""
}

calculate_duration() {
    local start=$1
    local end=$2
    local duration=$((end - start))
    local hours=$((duration / 3600))
    local minutes=$(((duration % 3600) / 60))
    local seconds=$((duration % 60))
    
    if [[ ${hours} -gt 0 ]]; then
        echo "${hours}h ${minutes}m ${seconds}s"
    elif [[ ${minutes} -gt 0 ]]; then
        echo "${minutes}m ${seconds}s"
    else
        echo "${seconds}s"
    fi
}

#-------------------------------------------------------------------------------
# MAIN
#-------------------------------------------------------------------------------

main() {
    SCRIPT_START_TIME=$(date +%s)
    
    parse_args "$@"
    
    # Créer le répertoire de log si nécessaire (avant toute autre opération)
    if [[ ! -d "${LOG_DIR}" ]] && [[ "${DRY_RUN}" != true ]]; then
        mkdir -p "${LOG_DIR}"
    fi
    
    # Charger les credentials email
    load_email_credentials
    
    # Mode status uniquement
    if [[ "${SHOW_STATUS}" == true ]]; then
        show_status
        exit 0
    fi
    
    # Mode rotation uniquement
    if [[ "${ROTATE_ONLY}" == true ]]; then
        echo ""
        echo "==============================================================================="
        echo "              ROTATION DES LOGS - PostgreSQL Backup"
        if [[ "${DRY_RUN}" == true ]]; then
            echo "                         🔍 MODE DRY-RUN 🔍"
        fi
        echo "==============================================================================="
        echo ""
        
        rotate_logs
        cleanup_old_logs
        
        echo ""
        log_success "Rotation des logs terminée"
        show_status
        
        exit 0
    fi
    
    echo ""
    echo "==============================================================================="
    echo "     BACKUP & RESTORE PostgreSQL - heron -> heron_formation"
    if [[ "${DRY_RUN}" == true ]]; then
        echo "                         🔍 MODE DRY-RUN 🔍"
    fi
    echo "==============================================================================="
    echo ""
    
    # Rotation des logs au démarrage si configuré
    if [[ "${LOG_ROTATE_ON_START}" == true ]]; then
        rotate_logs
    fi
    
    check_prerequisites
    check_password
    test_connections
    
    # Confirmation avant exécution (sauf si --yes ou --dry-run)
    if [[ "${AUTO_YES}" != true ]] && [[ "${DRY_RUN}" != true ]]; then
        echo ""
        echo "⚠️  ATTENTION: Ce script va:"
        echo "   1. Sauvegarder la base '${SOURCE_DB}' depuis ${SOURCE_HOST}:${SOURCE_PORT}"
        echo "   2. SUPPRIMER la base '${DEST_DB}' sur ${DEST_HOST}:${DEST_PORT}"
        echo "   3. Recréer et restaurer '${DEST_DB}' avec les données de '${SOURCE_DB}'"
        echo ""
        read -p "Continuer ? (oui/non) " -r response
        
        if [[ ! "${response}" =~ ^(oui|o|yes|y)$ ]]; then
            log_info "Opération annulée par l'utilisateur"
            exit 0
        fi
    fi
    
    echo ""
    
    # Exécution
    local backup_size="N/A"
    local status="SUCCESS"
    
    if backup_output=$(do_backup); then
        backup_size="${backup_output##*$'\n'}"
    else
        status="FAILURE"
    fi
    
    if [[ "${status}" == "SUCCESS" ]]; then
        drop_database || status="FAILURE"
    fi
    
    if [[ "${status}" == "SUCCESS" ]]; then
        create_database || status="FAILURE"
    fi
    
    if [[ "${status}" == "SUCCESS" ]]; then
        do_restore || status="PARTIAL"
    fi
    
    # Supprimer le dump après restauration réussie
    if [[ "${status}" == "SUCCESS" ]] || [[ "${status}" == "PARTIAL" ]]; then
        delete_dump_file
    fi
    
    cleanup_old_backups
    
    show_summary
    
    SCRIPT_END_TIME=$(date +%s)
    local duration=$(calculate_duration "${SCRIPT_START_TIME}" "${SCRIPT_END_TIME}")
    
    # Envoi de l'email de notification
    local email_subject=""
    if [[ "${DRY_RUN}" == true ]]; then
        email_subject="[DRY-RUN] Simulation terminée - ${SOURCE_DB} -> ${DEST_DB}"
    elif [[ "${status}" == "SUCCESS" ]]; then
        email_subject="✅ Succès - ${SOURCE_DB} -> ${DEST_DB}"
    elif [[ "${status}" == "PARTIAL" ]]; then
        email_subject="⚠️ Terminé avec warnings - ${SOURCE_DB} -> ${DEST_DB}"
    else
        email_subject="❌ Échec - ${SOURCE_DB} -> ${DEST_DB}"
    fi
    
    local email_body=$(build_email_body "${status}" "${duration}" "${backup_size}")
    send_email "${email_subject}" "${email_body}" "${status}"
    
    # Message final
    if [[ "${DRY_RUN}" == true ]]; then
        log_success "🔍 Simulation terminée (aucune opération effectuée)"
        echo ""
        echo "Pour exécuter réellement, relancer sans --dry-run"
    elif [[ "${status}" == "SUCCESS" ]]; then
        log_success "🎉 Opération terminée avec succès en ${duration}!"
    elif [[ "${status}" == "PARTIAL" ]]; then
        log_warn "⚠️ Opération terminée avec des warnings en ${duration}"
        exit 0
    else
        log_error "❌ Opération échouée après ${duration}"
        exit 1
    fi
}

# Point d'entrée
main "$@"
