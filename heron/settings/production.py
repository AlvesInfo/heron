from heron.settings.base import Path, INSTALLED_APPS, MIDDLEWARE, WHITELIST

DEBUG = False

DOMAINS_WHITELIST = ["localhost", "127.0.0.1", WHITELIST]

THIRD_PARTY_APPS = [
    "django_clamd",
]

INSTALLED_APPS += THIRD_PARTY_APPS

MIDDLEWARE = [] + MIDDLEWARE + []

# SESSION_COOKIE_AGE = 36000
# SESSION_EXPIRE_AT_BROWSER_CLOSE = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
# SESSION_SAVE_EVERY_REQUEST = True

# SECURE_CONTENT_TYPE_NOSNIFF = True
# SECURE_BROWSER_XSS_FILTER = True
# X_FRAME_OPTIONS = "DENY"

# SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
VAR_LOG_DIR = "/var/log/heron"

# log django.log
DJANGO_LOG = (Path(VAR_LOG_DIR) / "django.log").resolve()
Path.mkdir(DJANGO_LOG, exist_ok=True)

# log timer_heron.log
TIMER_HERON_LOG = (Path(VAR_LOG_DIR) / "timer_heron.log").resolve()
Path.mkdir(TIMER_HERON_LOG, exist_ok=True)

# log import_logfile.log
IMPORT_LOG = (Path(VAR_LOG_DIR) / "import_logfile.log").resolve()
Path.mkdir(IMPORT_LOG, exist_ok=True)

# log connect.log
GONNECT_LOG = (Path(VAR_LOG_DIR) / "connect.log").resolve()
Path.mkdir(GONNECT_LOG, exist_ok=True)

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
            "filename": f"{VAR_LOG_DIR}/django.log",
            "formatter": "verbose",
        },
        # Send in timer_heron
        "timer_heron": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": f"{VAR_LOG_DIR}/timer_heron.log",
            "formatter": "verbose",
        },
        # Send in import_logfile
        "import_logfile": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": f"{VAR_LOG_DIR}/import_logfile.log",
            "formatter": "verbose",
        },
        # Send in connexion_file
        "connexion": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": f"{VAR_LOG_DIR}/connect.log",
            "formatter": "simple",
        },
    },
    "loggers": {
        # all messages
        # 5xx ERRROR and 4xx WARNING
        "": {"handlers": ["console"], "propagate": True},
        "django": {"handlers": ["production_logfile"], "propagate": True},
        "production": {"handlers": ["production_logfile"], "propagate": True},
        "connect": {
            "handlers": ["connexion"],
            "propagate": True,
        },
        "timer_heron": {"handlers": ["timer_heron"]},
        "imports": {"handlers": ["import_logfile"], "propagate": False},
    },
}

MIDDLEWARE = [] + MIDDLEWARE + []

LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "accounts/logout/"

# DJANGO-CLAMD configuration
# https://pypi.org/project/django-clamd/
CLAMD_ENABLED = True
CLAMD_SOCKET = "/var/run/clamd/clamd.ctl"
CLAMD_USE_TCP = False
CLAMD_TCP_SOCKET = 3310
CLAMD_TCP_ADDR = "127.0.0.1"

ENVIRONNEMENT = "PRODUCTION"

# REPERTOIRE DU SERVEUR Sage X3
ACUITIS_EM_DIR = Path("/media/acuitis_edi")
ACUISENS_EM_DIR = Path("/media/acuisens_edi")
ACUITEST_EM_DIR = Path("/media/acuitest_edi")
ACUIREP_EM_DIR = Path("/media/acuirep_edi")
ACSENSREP_EM_DIR = Path("/media/acsensrep_edi")
