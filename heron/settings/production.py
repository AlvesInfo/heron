"""Réglages de production."""

import gc
import logging

from decouple import Csv

from heron.settings.base import INSTALLED_APPS, LOG_DIR, WHITELIST, Path, config

allocs, g1, g2 = gc.get_threshold()
gc.set_threshold(100_000, g1 * 5, g2 * 10)

DEBUG = False

# Domaine servant les statiques (polices, logos) aux PDF : obligatoire dans le .env de production
# (instance principale ou instance formation, chacune avec son propre .env)
PDF_STATIC_DOMAIN = config("PDF_STATIC_DOMAIN")

# Hôtes autorisés pour les redirections absolues (?next=) : ALLOWED_HOSTS + hôtes avec port
# déclarés dans DOMAINS_WHITELIST du .env (ex. instance formation :8080)
DOMAINS_WHITELIST = [*WHITELIST, *config("DOMAINS_WHITELIST", default="", cast=Csv())]

THIRD_PARTY_APPS = [
    "django_clamd",
]

INSTALLED_APPS += THIRD_PARTY_APPS

SESSION_COOKIE_AGE = 36000
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
# Durcissement https (cookies secure, HSTS, proxy SSL header, X-Frame-Options) volontairement
# absent : l'application est servie en http sur le réseau interne ; à activer avec le passage en https

# Origines de confiance CSRF (Django >= 4.0 compare l'en-tête Origin à l'hôte) : nécessaire
# seulement derrière un proxy qui change l'hôte ou le schéma, ex. https://heron.fr
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", default="", cast=Csv())

# AXES lockout responses on failed user authentication attempts from login views
# https://django-axes.readthedocs.io/en/latest/4_configuration.html
AXES_ENABLED = True
AXES_FAILURE_LIMIT = 5
# Verrouillage par utilisateur seul (ex AXES_ONLY_USER_FAILURES, django-axes >= 6)
AXES_LOCKOUT_PARAMETERS = ["username"]
# axes.W006 : le verrouillage par adresse IP est écarté volontairement, les agences partagent une
# même adresse publique (un compte bloqué ne doit pas bloquer les autres)
# security.W004/W008/W012/W016 : HSTS, redirection SSL et cookies secure sont volontairement absents
# tant que l'application est servie en http sur le réseau interne (voir ci-dessus) ; à retirer
# avec le passage en https
SILENCED_SYSTEM_CHECKS = [
    "axes.W006",
    "security.W004",
    "security.W008",
    "security.W012",
    "security.W016",
]
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
        "send_email": {
            "format": (
                "[send_email] : "
                "[%(asctime)s] %(levelname)s : %(message)s : "
                "%(filename)s : "
                "%(funcName)s : "
                "[ligne : %(lineno)s] : "
                "%(process)d : "
                "%(thread)d"
            ),
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "export_x3": {
            "format": (
                "[export_x3] : "
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
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        # Send in production_logfile
        "production_logfile": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": f"{LOG_DIR!s}/django.log",
            "formatter": "verbose",
        },
        # Send in timer_heron
        "timer_heron": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": f"{LOG_DIR!s}/timer_heron.log",
            "formatter": "verbose",
        },
        # envoi vers import_logfile
        "import_logfile": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": f"{LOG_DIR!s}/import_logfile.log",
            "formatter": "verbose",
        },
        # envoi vers import_logfile
        "edi_logfile": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": f"{LOG_DIR!s}/edi_logfile.log",
            "formatter": "verbose",
        },
        # Send it in a connexion-file
        "connexion-file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": f"{LOG_DIR!s}/connexion.log",
            "formatter": "verbose",
        },
        # error_views
        "error_views": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": f"{LOG_DIR!s}/error_views.log",
            "formatter": "verbose",
        },
        # export_excel
        "export_excel": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": f"{LOG_DIR!s}/export_excel.log",
            "formatter": "verbose",
        },
        # Send in loader data_flux
        "loader_logfile_flux": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": f"{LOG_DIR!s}/loaders_flux.log",
            "formatter": "data_flux",
        },
        # Send in validation data_flux
        "validation_logfile_flux": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": f"{LOG_DIR!s}/validation_flux.log",
            "formatter": "data_flux",
        },
        # Send in postgres_save data_flux
        "postgres_save_logfile_flux": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": f"{LOG_DIR!s}/postgres_save_flux.log",
            "formatter": "data_flux",
        },
        # Send in invoices generation or printing
        "invoices_flux": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": f"{LOG_DIR!s}/invoices_flux.log",
            "formatter": "invoices_flux",
        },
        # Send in send email
        "send_email": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": f"{LOG_DIR!s}/send_email.log",
            "formatter": "send_email",
        },
        # export files X3
        "export_x3": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": f"{LOG_DIR!s}/export_files_x3.log",
            "formatter": "export_x3",
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
            "propagate": False,
        },
        "timer_heron": {"handlers": ["timer_heron"]},
        "imports": {"handlers": ["import_logfile"], "propagate": True},
        "edi": {"handlers": ["edi_logfile"], "propagate": True},
        "error_views": {"handlers": ["error_views"], "propagate": True},
        "export_excel": {"handlers": ["export_excel"], "propagate": True},
        "loader": {"handlers": ["loader_logfile_flux"], "propagate": True},
        "validation": {"handlers": ["validation_logfile_flux"], "propagate": True},
        "postgres_save": {
            "handlers": ["postgres_save_logfile_flux"],
            "propagate": True,
        },
        "invoices_flux": {"handlers": ["invoices_flux"], "propagate": True},
        "send_email": {"handlers": ["send_email"], "propagate": True},
        "export_x3": {"handlers": ["export_x3"], "propagate": True},
        # Réduire les logs de fontTools (WeasyPrint font subsetting)
        "fontTools": {"level": "ERROR", "propagate": False},
        "fontTools.subset": {"level": "ERROR", "propagate": False},
        # Réduire les logs de WeasyPrint
        "weasyprint": {"level": "ERROR", "propagate": False},
        "weasyprint.css": {"level": "ERROR", "propagate": False},
    },
}

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


# Réduire le niveau de log pour WeasyPrint
logging.getLogger("weasyprint").setLevel(logging.ERROR)

# Ou pour désactiver complètement les warnings CSS
logging.getLogger("weasyprint.css").setLevel(logging.ERROR)

# Réduire le niveau de log pour fonttools (utilisé par WeasyPrint pour le subsetting des polices)
logging.getLogger("fontTools").setLevel(logging.ERROR)
logging.getLogger("fontTools.subset").setLevel(logging.ERROR)
