# coding: utf-8
from pathlib import Path
from .base import INSTALLED_APPS, MIDDLEWARE, BASE_DIR, LOG_DIR

DEBUG = True

INTERNAL_IPS = ["10.185.51.9", "localhost", "127.0.0.1"]

DOMAINS_WHITELIST = ["10.185.51.9", "localhost", "127.0.0.1"]

THIRD_PARTY_APPS = ["debug_toolbar"]

INSTALLED_APPS += THIRD_PARTY_APPS

MIDDLEWARE = (
    ["debug_toolbar.middleware.DebugToolbarMiddleware"]
    + MIDDLEWARE
    + []
)

LOG_FILE = (Path(LOG_DIR) / "developpement.log").resolve()
LOG_EDI_FILE = (Path(LOG_DIR) / "edi_file.log").resolve()
LOG_IMPORT_FILE = (Path(LOG_DIR) / "import_file.log").resolve()
LOG_CONNEXION = (Path(LOG_DIR) / "connexion.log").resolve()
LOG_ERROR_VIEWS = (Path(LOG_DIR) / "error_views.log").resolve()
LOG_EXPORT_ECEL = (Path(LOG_DIR) / "export_excel.log").resolve()

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": (
                "[heron] : "
                "[%(asctime)s] %(levelname)s : %(message)s : "
                "%(filename)s : "
                "%(funcName)s : "
                "[ligne : %(lineno)s] : "
                "%(process)d : "
                "%(thread)d"
            ),
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {
            "format": "[%(asctime)s] %(levelname)s : %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        # Send in console
        "console": {"level": "INFO", "class": "logging.StreamHandler", "formatter": "simple"},
        # Send in development_logfile
        "production_logfile": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": LOG_FILE,
            "formatter": "verbose",
        },
        # Send in import_logfile
        "import_logfile": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": LOG_IMPORT_FILE,
            "formatter": "verbose",
        },
        # Send in import_logfile
        "edi_logfile": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": LOG_EDI_FILE,
            "formatter": "verbose",
        },
        # Send in connexion-file
        "connexion-file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": LOG_CONNEXION,
            "formatter": "verbose",
        },
        # error_views
        "error_views": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": LOG_ERROR_VIEWS,
            "formatter": "verbose",
        },
        # export_excel
        "export_excel": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": LOG_EXPORT_ECEL,
            "formatter": "verbose",
        },
    },
    "loggers": {
        # all messages
        # 5xx ERRROR and 4xx WARNING
        "": {"handlers": ["console"], "propagate": True},
        "django": {"handlers": ["production_logfile"], "propagate": True},
        "imports": {"handlers": ["import_logfile"], "level": "WARNING", "propagate": True},
        "connexion": {"handlers": ["connexion-file"], "level": "INFO", "propagate": True},
        "edi": {"handlers": ["edi_logfile"], "propagate": True},
        "error_views": {"handlers": ["error_views"], "propagate": True},
        "export_excel": {"handlers": ["export_excel"], "propagate": True},
    },
}

ENVIRONNEMENT = "LOCAL"

# REPERTOIRE DU SERVEUR Sage X3
ACUITIS_EM_DIR = Path("U:\\")
ACUITIS_ARCHIVE_EM_DIR = Path("U:\\ARCHIVE")
ACUISENS_EM_DIR = Path("V:\\")
ACUITEST_EM_DIR = Path("W:\\")
ACUIREP_EM_DIR = Path("X:\\")
ACSENSREP_EM_DIR = Path("Z:\\")
