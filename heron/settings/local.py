# coding: utf-8
from pathlib import Path
import gc

from heron.settings.base import INSTALLED_APPS, MIDDLEWARE, LOG_DIR

allocs, g1, g2 = gc.get_threshold()
gc.set_threshold(100_000, g1*5, g2*10)

DEBUG = True

INTERNAL_IPS = ["10.9.2.109", "10.9.2.109:8080", "localhost", "127.0.0.1", "localhost:8080", "127.0.0.1:8080"]

DOMAINS_WHITELIST = ["10.9.2.109", "10.9.2.109:8080", "localhost", "127.0.0.1", "localhost:8080", "127.0.0.1:8080"]

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
        "data_flux": {
            "format": (
                "[data_flux] : "
                "[%(asctime)s] %(levelname)s : %(message)s : "
                "%(filename)s : "
                "%(funcName)s : "
                "[ligne : %(lineno)s] : "
                "%(process)d : "
                "%(thread)d"
            ),
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "invoices_flux": {
            "format": (
                "[invoices] : "
                "[%(asctime)s] %(levelname)s : %(message)s : "
                "%(filename)s : "
                "%(funcName)s : "
                "[ligne : %(lineno)s] : "
                "%(process)d : "
                "%(thread)d"
            ),
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
            "formatter": "simple",
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
        # Send in loader data_flux
        "loader_logfile_flux": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": f"{str(LOG_DIR)}/loaders_flux.log",
            "formatter": "data_flux",
        },
        # Send in validation data_flux
        "validation_logfile_flux": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": f"{str(LOG_DIR)}/validation_flux.log",
            "formatter": "data_flux",
        },
        # Send in postgres_save data_flux
        "postgres_save_logfile_flux": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": f"{str(LOG_DIR)}/postgres_save_flux.log",
            "formatter": "data_flux",
        },
        # Send in timer_heron
        "timer_heron": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": f"{str(LOG_DIR)}/timer_heron.log",
            "formatter": "verbose",
        },
        # Send in invoices generation or printing
        "invoices_flux": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": f"{str(LOG_DIR)}/invoices_flux.log",
            "formatter": "invoices_flux",
        },
    },
    "loggers": {
        # all messages
        # 5xx ERRROR and 4xx WARNING
        "": {"handlers": ["console"], "propagate": True},
        "django": {"handlers": ["production_logfile"], "propagate": True},
        "production": {"handlers": ["production_logfile"], "propagate": True},
        "connexion": {"handlers": ["connexion-file"], "level": "INFO", "propagate": False},
        "timer_heron": {"handlers": ["timer_heron"]},
        "imports": {"handlers": ["import_logfile"], "propagate": True},
        "edi": {"handlers": ["edi_logfile"], "propagate": True},
        "error_views": {"handlers": ["error_views"], "propagate": True},
        "export_excel": {"handlers": ["export_excel"], "propagate": True},
        "loader": {"handlers": ["loader_logfile_flux"], "propagate": True},
        "validation": {"handlers": ["validation_logfile_flux"], "propagate": True},
        "postgres_save": {"handlers": ["postgres_save_logfile_flux"], "propagate": True},
        "invoices_flux": {"handlers": ["invoices_flux"], "propagate": True},
        "send_email": {"handlers": ["invoices_flux"], "propagate": True},
        "export_x3": {"handlers": ["invoices_flux"], "propagate": True},
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

# Réduire le niveau de log pour WeasyPrint
logging.getLogger("weasyprint").setLevel(logging.ERROR)

# Ou pour désactiver complètement les warnings CSS
logging.getLogger("weasyprint.css").setLevel(logging.ERROR)

# Réduire le niveau de log pour fonttools (utilisé par WeasyPrint pour le subsetting des polices)
logging.getLogger("fontTools").setLevel(logging.ERROR)
logging.getLogger("fontTools.subset").setLevel(logging.ERROR)
