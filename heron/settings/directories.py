from pathlib import Path
from heron.utils.directories import lazy_mkdir, get_files_base_dir

FILES_BASE_DIR = get_files_base_dir()

# REPERTOIRE DES FICHIERS
FILES_DIR = lazy_mkdir("files")

# REPERTOIRE DES BACKUP (SAUVEGARDE)
BACKUP_DIR = lazy_mkdir("files/backup")

# REPERTOIRE DES BACKUP SAGE
BACKUP_SAGE_DIR = lazy_mkdir("files/backup/sage")

# REPERTOIRES DE MEDIA
MEDIA_DIR = lazy_mkdir("files/media")

# REPERTOIRES DES FICHIERS EXCEL
MEDIA_EXCEL_FILES_DIR = lazy_mkdir("files/media/excel_files")

# REPERTOIRES DES FICHIERS EXCEL
SALES_INVOICES_FILES_DIR = lazy_mkdir("files/media/sales_invoices")

# REPERTOIRES DES PICKLERS
PICKLERS_DIR = lazy_mkdir("files/media/pickler")

# REPERTOIRES DE STATIC
STATIC_DIR = lazy_mkdir("files/static")

# REPERTOIRES DE TRAITEMENTS
PROCESSING_DIR = lazy_mkdir("files/processing")

# REPERTOIRES DE TRAITEMENTS DES IMPORTS DE FICHIERS SAGE
PROCESSING_SAGE_DIR = lazy_mkdir("files/processing/sage")

# REPERTOIRES DE TRAITEMENTS DES FACTURES FOURNISSEURS
PROCESSING_SUPPLIERS_DIR = lazy_mkdir("files/processing/suppliers_invoices_files")

# REPERTOIRE DE TRAITEMENT DES IMPORTS DES ARTICLES SANS COMPTES
PROCESSING_WITHOUT_ACCOUNT_DIR = lazy_mkdir("files/processing/suppliers_invoices_files/ARTICLES_SANS_COMPTES")

# REPERTOIRE DE TRAITEMENT DES IMPORTS DESABONNEMENTS PAR MAISONS
PROCESSING_CLIENS_SUBSCRIPTION = lazy_mkdir("files/processing/suppliers_invoices_files/ABONNEMENTS_PAR_MAISONS")

# REPERTOIRE DE TRAITEMENT DES OD A PASSER
PROCESSING_OD_A_PASSER = lazy_mkdir("files/processing/suppliers_invoices_files/OD_A_PASSER")

# REPERTOIRE DES FICHIERS A EXPORTER
EXPORT_DIR = lazy_mkdir("files/media/export")

# REPERTOIRE DES SORTIES EXCEL
EXCEL_DIR = lazy_mkdir("files/excel")

# REPERTOIRE DES IMPRESSIONS
PRINTING_DIR = lazy_mkdir("files/printing")

# REPERTOIRE DES FICHIERS EN ERREUR
ERRORS_DIR = lazy_mkdir("files/errors")

# REPERTOIRE SECURE MEDIA
SECURE_MEDIA_ROOT = lazy_mkdir("files/secure_media")

# REPERTOIRE STATIC
STATIC_ROOT = lazy_mkdir("files/static")

# REPERTOIRES statics
STATIC_URL = "static/"
