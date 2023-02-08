from pathlib import Path

FILES_BASE_DIR = Path(__file__).resolve().parent.parent.parent

# REPERTOIRE DES FICHIERS
FILES_DIR = (Path(FILES_BASE_DIR) / "files").resolve()
Path.mkdir(FILES_DIR, exist_ok=True)

# REPERTOIRE DES BACKUP (SAUVEGARDE)
BACKUP_DIR = (Path(FILES_BASE_DIR) / "files/backup").resolve()
Path.mkdir(BACKUP_DIR, exist_ok=True)

# REPERTOIRE DES BACKUP SAGE
BACKUP_SAGE_DIR = (Path(FILES_BASE_DIR) / "files/backup/sage").resolve()
Path.mkdir(BACKUP_SAGE_DIR, exist_ok=True)

# REPERTOIRES DE MEDIA
MEDIA_DIR = (Path(FILES_BASE_DIR) / "files/media").resolve()
Path.mkdir(MEDIA_DIR, exist_ok=True)

# REPERTOIRES DE MEDIA
MEDIA_EXCEL_FILES_DIR = (Path(FILES_BASE_DIR) / "files/media/excel_files").resolve()
Path.mkdir(MEDIA_EXCEL_FILES_DIR, exist_ok=True)

# REPERTOIRES DES PICKLERS
PICKLERS_DIR = (Path(FILES_BASE_DIR) / "files/media/pickler").resolve()
Path.mkdir(PICKLERS_DIR, exist_ok=True)

# REPERTOIRES DE STATIC
STATIC_DIR = (Path(FILES_BASE_DIR) / "files/static").resolve()
Path.mkdir(STATIC_DIR, exist_ok=True)

# REPERTOIRES DE TRAITEMENTS
PROCESSING_DIR = (Path(FILES_BASE_DIR) / "files/processing").resolve()
Path.mkdir(PROCESSING_DIR, exist_ok=True)

# REPERTOIRES DE TRAITEMENTS DES IMPORTS DE FICHIERS SAGE
PROCESSING_SAGE_DIR = (Path(FILES_BASE_DIR) / "files/processing/sage").resolve()
Path.mkdir(PROCESSING_SAGE_DIR, exist_ok=True)

# REPERTOIRES DE TRAITEMENTS DES FACTURES FOURNISSEURS
PROCESSING_SUPPLIERS_DIR = (
    Path(FILES_BASE_DIR) / "files/processing/suppliers_invoices_files"
).resolve()
Path.mkdir(PROCESSING_SUPPLIERS_DIR, exist_ok=True)

# REPERTOIRE DES FICHIERS A EXPORTER
EXPORT_DIR = (Path(FILES_BASE_DIR) / "files/export").resolve()
Path.mkdir(EXPORT_DIR, exist_ok=True)

# REPERTOIRE DES SORTIES EXCEL
EXCEL_DIR = (Path(FILES_BASE_DIR) / "files/excel").resolve()
Path.mkdir(EXCEL_DIR, exist_ok=True)

# REPERTOIRE DES IMPRESSIONS
PRINTING_DIR = (Path(FILES_BASE_DIR) / "files/printing").resolve()
Path.mkdir(PRINTING_DIR, exist_ok=True)

# REPERTOIRE DES FICHIERS EN ERREUR
ERRORS_DIR = (Path(FILES_BASE_DIR) / "files/errors").resolve()
Path.mkdir(ERRORS_DIR, exist_ok=True)

# REPERTOIRE SECURE MEDIA
SECURE_MEDIA_ROOT = (Path(FILES_BASE_DIR) / "files/secure_media").resolve()
Path.mkdir(SECURE_MEDIA_ROOT, exist_ok=True)

# REPERTOIRE STATIC
STATIC_ROOT = (Path(FILES_BASE_DIR) / "files/static").resolve()
Path.mkdir(STATIC_ROOT, exist_ok=True)

# REPERTOIRES statics
STATIC_URL = "/static/"
STATIC_ROOT = (Path(FILES_BASE_DIR) / "files/static").resolve()
