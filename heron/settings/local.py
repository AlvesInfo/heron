# coding: utf-8
from pathlib import Path
from .base import INSTALLED_APPS, MIDDLEWARE, os, BASE_DIR, LOG_DIR

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

STATIC_URL = "/static/"
STATIC_ROOT = os.path.realpath(os.path.join(BASE_DIR, "files/static"))

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.realpath(os.path.join(BASE_DIR, "files/media"))

LOG_FILE = Path(LOG_DIR) / "developpement.log"
LOG_IMPORT_FILE = Path(LOG_DIR) / "import_file.log"
LOG_CONNEXION = Path(LOG_DIR) / "connection.log"

AUTHENTICATION_BACKENDS = [
    # AxesBackend should be the first backend in the AUTHENTICATION_BACKENDS list.
    "axes.backends.AxesBackend",
    # Django ModelBackend is the default authentication backend.
    "django.contrib.auth.backends.ModelBackend",
]


# AXES lockout responses on failed user authentication attempts from login views
# https://django-axes.readthedocs.io/en/latest/4_configuration.html
AXES_ENABLED = True
AXES_FAILURE_LIMIT = 5
AXES_ONLY_USER_FAILURES = True
AXES_LOCKOUT_TEMPLATE = "axes_blocked.html"
AXES_USERNAME_FORM_FIELD = "email"

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
            "filename": str(LOG_FILE),
            "formatter": "verbose",
        },
        # Send in import_logfile
        "import_logfile": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": str(LOG_IMPORT_FILE),
            "formatter": "verbose",
        },
        # Send in connexion-file
        "connexion-file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": str(LOG_CONNEXION),
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
