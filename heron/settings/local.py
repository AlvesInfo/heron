# coding: utf-8
from pathlib import Path
from .base import INSTALLED_APPS, MIDDLEWARE, BASE_DIR, LOG_DIR

DEBUG = True

INTERNAL_IPS = ["localhost", "127.0.0.1"]

DOMAINS_WHITELIST = ["localhost", "127.0.0.1"]

THIRD_PARTY_APPS = ["debug_toolbar"]

INSTALLED_APPS += THIRD_PARTY_APPS

MIDDLEWARE = (
    ["debug_toolbar.middleware.DebugToolbarMiddleware"]
    + MIDDLEWARE
    + ["axes.middleware.AxesMiddleware"]
)

LOG_FILE = (Path(LOG_DIR) / "developpement.log").resolve()
LOG_IMPORT_FILE = (Path(LOG_DIR) / "import_file.log").resolve()
LOG_CONNEXION = (Path(LOG_DIR) / "connection.log").resolve()

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
        # Send in connexion-file
        "connexion-file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": LOG_CONNEXION,
            "formatter": "verbose",
        },
    },
    "loggers": {
        # all messages
        # 5xx ERRROR and 4xx WARNING
        "": {"handlers": ["console"], "propagate": True},
        "django": {"handlers": ["production_logfile"], "propagate": True},
        "imports": {"handlers": ["import_logfile"], "level": "WARNING", "propagate": False},
        "connexion": {"handlers": ["connexion-file"], "level": "INFO", "propagate": False},
    },
}

ENVIRONNEMENT = "LOCAL"

AXES_ENABLED = False
