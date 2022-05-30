from heron.settings.base import Path, INSTALLED_APPS, MIDDLEWARE, WHITELIST

DEBUG = False

DOMAINS_WHITELIST = ["10.185.51.9", "localhost", "127.0.0.1", WHITELIST]

THIRD_PARTY_APPS = [
    "django_clamd",
]

INSTALLED_APPS += THIRD_PARTY_APPS

MIDDLEWARE = [] + MIDDLEWARE + ["axes.middleware.AxesMiddleware"]

SESSION_COOKIE_AGE = 36000
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
# SESSION_SAVE_EVERY_REQUEST = True

# SECURE_CONTENT_TYPE_NOSNIFF = True
# SECURE_BROWSER_XSS_FILTER = True
# X_FRAME_OPTIONS = "DENY"

# SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

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
AXES_LOCKOUT_TEMPLATE = 'axes_blocked.html'
AXES_USERNAME_FORM_FIELD = "email"

# LOG DIRECTORY
VAR_LOG_DIR = Path("/var/log/heron").resolve()
Path.mkdir(VAR_LOG_DIR, exist_ok=True)

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
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        # Send in production_logfile
        "production_logfile": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": f"{str(VAR_LOG_DIR)}/django.log",
            "formatter": "verbose",
        },
        # Send in timer_heron
        "timer_heron": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": f"{str(VAR_LOG_DIR)}/timer_heron.log",
            "formatter": "verbose",
        },
        # Send in import_logfile
        "import_logfile": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": f"{str(VAR_LOG_DIR)}/import_logfile.log",
            "formatter": "verbose",
        },
        # Send in import_logfile
        "edi_logfile": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": f"{str(VAR_LOG_DIR)}/edi_logfile.log",
            "formatter": "verbose",
        },
        # Send in connexion-file
        "connexion-file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": f"{str(VAR_LOG_DIR)}/connexion.log",
            "formatter": "simple",
        },
        # error_views
        "error_views": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": f"{str(VAR_LOG_DIR)}/error_views.log",
            "formatter": "verbose",
        },
        # export_excel
        "export_excel": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": f"{str(VAR_LOG_DIR)}/export_excel.log",
            "formatter": "verbose",
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
ACUITIS_ARCHIVE_EM_DIR = Path("/media/acuitis_edi/ARCHIVE")
ACUISENS_EM_DIR = Path("/media/acuisens_edi")
ACUITEST_EM_DIR = Path("/media/acuitest_edi")
ACUIREP_EM_DIR = Path("/media/acuirep_edi")
ACSENSREP_EM_DIR = Path("/media/acsensrep_edi")
