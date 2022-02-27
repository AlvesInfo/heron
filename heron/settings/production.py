# coding: utf-8
from pathlib import Path
from .base import os, INSTALLED_APPS, MIDDLEWARE, BASE_DIR, LOG_DIR, WHITELIST

DEBUG = False

DOMAINS_WHITELIST = ["localhost", "127.0.0.1", WHITELIST]

THIRD_PARTY_APPS = [
    "django_clamd",
]

INSTALLED_APPS += THIRD_PARTY_APPS

MIDDLEWARE = [] + MIDDLEWARE + ["axes.middleware.AxesMiddleware"]

STATIC_URL = "/static/"
STATIC_ROOT = os.path.realpath(os.path.join(BASE_DIR, "files/static"))

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "files/static/css"),
    os.path.join(BASE_DIR, "files/static/js"),
    os.path.join(BASE_DIR, "files/static/images"),
    os.path.join(BASE_DIR, "files/static/fonts"),
    os.path.join(BASE_DIR, "files/static/vendor"),
]

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.realpath(os.path.join(BASE_DIR, "files/media"))

SESSION_COOKIE_AGE = 36000
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True

# SECURE_CONTENT_TYPE_NOSNIFF = True
# SECURE_BROWSER_XSS_FILTER = True
# X_FRAME_OPTIONS = "DENY"

# SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
heron_DIR_LOG = str(LOG_DIR) if DEBUG else "/var/log/heron"

AUTHENTICATION_BACKENDS = [
    # AxesBackend should be the first backend in the AUTHENTICATION_BACKENDS list.
    "axes.backends.AxesBackend",
    # Django ModelBackend is the default authentication backend.
    "django.contrib.auth.backends.ModelBackend",
    # OIDC ModelBackend
    # "apps.users.oidc_backend.heronOidcuserBackend",
]

# AXES lockout responses on failed user authentication attempts from login views
# https://django-axes.readthedocs.io/en/latest/4_configuration.html
AXES_ENABLED = True
AXES_FAILURE_LIMIT = 5
AXES_ONLY_USER_FAILURES = True
AXES_LOCKOUT_TEMPLATE = 'axes_blocked.html'
AXES_USERNAME_FORM_FIELD = "email"

LOG_IMPORT_FILE = Path(LOG_DIR) / "import_file.log"

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
            "format": "[heron] : [%(asctime)s] %(levelname)s : %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        # Send in console
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        # Send in production_logfile
        "production_logfile": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": f"{heron_DIR_LOG}/django.log",
            "formatter": "verbose",
        },
        # Send in logger_oidc
        "logger_oidc": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": f"{heron_DIR_LOG}/oidc.log",
            "formatter": "verbose",
        },
        # Send in timer_heron
        "timer_heron": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": f"{heron_DIR_LOG}/timer_heron.log",
            "formatter": "verbose",
        },
        # Send in import_logfile
        "import_logfile": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": f"{heron_DIR_LOG}/import_logfile.log",
            "formatter": "verbose",
        },
        # Send in connexion-file
        "connexion-file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": f"{heron_DIR_LOG}/connect.log",
            "formatter": "simple",
        },
    },
    "loggers": {
        # all messages
        # 5xx ERRROR and 4xx WARNING
        "": {"handlers": ["console"], "propagate": True},
        "django": {"handlers": ["production_logfile"], "propagate": True},
        "production": {"handlers": ["production_logfile"], "propagate": True},
        "connexion": {
            "handlers": ["connexion-file"],
            "level": "INFO",
            "propagate": True,
        },
        "mozilla_django_oidc": {"handlers": ["logger_oidc"], "level": "DEBUG"},
        "timer_heron": {"handlers": ["timer_heron"], "level": "DEBUG"},
        "imports": {"handlers": ["import_logfile"], "level": "WARNING", "propagate": False},
    },
}

# Configuration de Mozilla django-oidc pour ProSanteConnect

# Si l'on doit appliquer la connexion par ProSanteConnect
# ENVIRONNEMENT doit passer à ENVIRONNEMENT = "PRODUCTION"
ENVIRONNEMENT = "LOCAL"

# A REMETTRE SI PASSAGE A PRO SANTE CONNECT
# FOUR_PARTY_APPS += ["mozilla_django_oidc"]
# INSTALLED_APPS += FOUR_PARTY_APPS

MIDDLEWARE = [] + MIDDLEWARE + []

LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "accounts/logout/"

# DJANGO-CLAMD configuration
# https://pypi.org/project/django-clamd/
CLAMD_ENABLED = True
CLAMD_SOCKET = "/var/run/clamd.scan/clamd.sock"
CLAMD_USE_TCP = False
CLAMD_TCP_SOCKET = 3310
CLAMD_TCP_ADDR = "127.0.0.1"
