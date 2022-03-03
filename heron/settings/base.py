# pylint: disable=E0401
"""
Django settings for heron project.
"""
import sys
from pathlib import Path

from decouple import Csv, AutoConfig
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_DIR = Path(__file__).resolve().parent.parent
APPS_DIR = (Path(BASE_DIR) / "apps").resolve()
CORE_DIR = (Path(BASE_DIR) / "apps").resolve()

# print(BASE_DIR, PROJECT_DIR, APPS_DIR, CORE_DIR, sep=" | ")

sys.path.append(str(BASE_DIR))
sys.path.append(str(PROJECT_DIR))
sys.path.append(str(APPS_DIR))
sys.path.append(str(CORE_DIR))

path_env = (Path(PROJECT_DIR) / "env/.env").resolve()
config = AutoConfig(search_path=path_env)

SECRET_KEY = config("SECRET_KEY")

EMAIL_HOST = config("EMAIL_HOST", default="localhost")
EMAIL_PORT = config("EMAIL_PORT", default=25, cast=int)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="admin@asipsante.fr")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default=None)
EMAIL_USE_SSL = config("EMAIL_USE_SSL", default=True, cast=bool)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=False, cast=bool)

EMAIL_DEV = config("EMAIL_HOST_USER", default="admin@asipsante.fr")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="admin@asipsante.fr")

NAME_DATABASE = config("NAME_DATABASE")
USER_DATABASE = config("USER_DATABASE")
PASSWORD_DATABASE = config("PASSWORD_DATABASE")
HOST_DATABASE = config("HOST_DATABASE")
PORT_DATABASE = config("PORT_DATABASE")

NAME_DATABASE_BI = config("NAME_DATABASE_BI")
USER_DATABASE_BI = config("USER_DATABASE_BI")
PASSWORD_DATABASE_BI = config("PASSWORD_DATABASE_BI")
HOST_DATABASE_BI = config("HOST_DATABASE_BI")
PORT_DATABASE_BI = config("PORT_DATABASE_BI")

ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv())

WHITELIST = config("ALLOWED_HOSTS", cast=Csv())

# Application definition
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.humanize",
]

THIRD_PARTY_APPS = [
    # "rest_framework",
    # "rest_framework.authtoken",
    "django_filters",
    "django_extensions",
    "crispy_forms",
    "crispy_forms_semantic_ui",
    "axes",
    "ckeditor",
    "chartjs",
]

LOCAL_APPS = [
    "core",
    "heron",
    "apps.articles",
    "apps.business_centers",
    "apps.centers_purchasing",
    "apps.clients_book",
    "apps.clients_invoices",
    "apps.clients_validations",
    "apps.countries",
    "apps.groups",
    "apps.parameters",
    "apps.periods",
    "apps.permissions",
    "apps.suppliers_book",
    "apps.suppliers_invoices",
    "apps.suppliers_validations",
    "apps.users",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # "axes.middleware.AxesMiddleware",
]

ROOT_URLCONF = "heron.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            # Path(PROJECT_DIR) / "templates",
            # Path(CORE_DIR) / "templates",
            # Path(APPS_DIR) / "templates",
            # Path(BASE_DIR) / "heron/templates/heron",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "heron.processors.title",
                "heron.processors.user_group",
                "heron.processors.groups_processor",
                "heron.processors.groupes_processor",
                "heron.processors.date_du_jour",
                "heron.processors.annee_du_jour",
                "heron.processors.debug",
            ]
        },
    }
]

WSGI_APPLICATION = "heron.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": NAME_DATABASE,
        "USER": USER_DATABASE,
        "PASSWORD": PASSWORD_DATABASE,
        "HOST": HOST_DATABASE,
        "PORT": PORT_DATABASE,
        "client_encoding": "UTF8",
    },
    "bi_bdd": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": NAME_DATABASE_BI,
        "USER": USER_DATABASE_BI,
        "PASSWORD": PASSWORD_DATABASE_BI,
        "HOST": HOST_DATABASE_BI,
        "PORT": PORT_DATABASE_BI,
        "client_encoding": "UTF8",
    },
}

AUTHENTICATION_BACKENDS = [
    # AxesBackend should be the first backend in the AUTHENTICATION_BACKENDS list.
    "axes.backends.AxesBackend",
    # Django ModelBackend is the default authentication backend.
    "django.contrib.auth.backends.ModelBackend",
]

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "users.User"

SITE_ID = 2

LANGUAGE_CODE = "fr-FR"
LANGUAGES = [("fr", _("French"))]
TIME_ZONE = "Europe/Paris"
SHORT_DATE_FORMAT = "d/m/Y"
DATE_FORMAT = "d/m/Y"
DATE_INPUT_FORMATS = [
    "%d-%m-%Y",
    "%d/%m/%Y",
    "%d/%m/%y",  # '2006-10-25', '10/25/2006', '10/25/06'
    "%d %b %Y",
    "%d %b, %Y",  # '25 Oct 2006', '25 Oct, 2006'
    "%d %B %Y",
    "%d %B, %Y",  # '25 October 2006', '25 October, 2006'
]

USE_I18N = True
USE_L10N = True
USE_TZ = True

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ("rest_framework.authentication.TokenAuthentication",),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.AllowAny",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 20,
}

DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000

# REPERTOIRE DES FICHIERS
FILES_DIR = (Path(BASE_DIR) / "files").resolve()
Path.mkdir(FILES_DIR, exist_ok=True)

# REPERTOIRE DES FICHIERS
IMAGES_DIR = Path(BASE_DIR / "files/static/images").resolve()
Path.mkdir(IMAGES_DIR, exist_ok=True)

# REPERTOIRE DES BACKUP (SAUVEGARDE)
BACKUP_DIR = (Path(BASE_DIR) / "files/backup").resolve()
Path.mkdir(BACKUP_DIR, exist_ok=True)

# REPERTOIRES DE MEDIA
MEDIA_DIR = (Path(BASE_DIR) / "files/media").resolve()
Path.mkdir(MEDIA_DIR, exist_ok=True)

# REPERTOIRES DE STATIC
STATIC_DIR = (Path(BASE_DIR) / "files/static").resolve()
Path.mkdir(STATIC_DIR, exist_ok=True)

# REPERTOIRES DE TRAITEMENTS
PROCESSING_DIR = (Path(BASE_DIR) / "files/processing").resolve()
Path.mkdir(PROCESSING_DIR, exist_ok=True)

# REPERTOIRE DES FICHIERS A EXPORTER
EXPORT_DIR = (Path(BASE_DIR) / "files/export").resolve()
Path.mkdir(EXPORT_DIR, exist_ok=True)

# REPERTOIRE DES SORTIES EXCEL
EXCEL_DIR = (Path(BASE_DIR) / "files/excel").resolve()
Path.mkdir(EXCEL_DIR, exist_ok=True)

# REPERTOIRE DES IMPRESSIONS
PRINTING_DIR = (Path(BASE_DIR) / "files/printing").resolve()
Path.mkdir(PRINTING_DIR, exist_ok=True)

# REPERTOIRE DES LOGS
LOG_DIR = (Path(BASE_DIR) / "files/log").resolve()
Path.mkdir(LOG_DIR, exist_ok=True)

# REPERTOIRE DES FICHIERS EN ERREUR
ERRORS_DIR = (Path(BASE_DIR) / "files/errors").resolve()
Path.mkdir(ERRORS_DIR, exist_ok=True)

# REPERTOIRE SECURE MEDIA
SECURE_MEDIA_ROOT = (Path(BASE_DIR) / "files/secure_media").resolve()
Path.mkdir(SECURE_MEDIA_ROOT, exist_ok=True)

# REPERTOIRE STATIC
STATIC_ROOT = (Path(BASE_DIR) / "files/static").resolve()
Path.mkdir(STATIC_ROOT, exist_ok=True)

# REPERTOIRES statics
STATIC_URL = "/static/"
STATIC_ROOT = (Path(BASE_DIR) / "files/static").resolve()

Path.mkdir(BASE_DIR / "files/static/css", exist_ok=True)
Path.mkdir(BASE_DIR / "files/static/js", exist_ok=True)
Path.mkdir(BASE_DIR / "files/static/img", exist_ok=True)
Path.mkdir(BASE_DIR / "files/static/fonts", exist_ok=True)
Path.mkdir(BASE_DIR / "files/static/vendor", exist_ok=True)

STATICFILES_DIRS = [
    (Path(BASE_DIR) / "files/static/css").resolve(),
    (Path(BASE_DIR) / "files/static/js").resolve(),
    (Path(BASE_DIR) / "files/static/img").resolve(),
    (Path(BASE_DIR) / "files/static/fonts").resolve(),
    (Path(BASE_DIR) / "files/static/vendor").resolve(),
]

MEDIA_URL = "media/"
MEDIA_ROOT = (Path(BASE_DIR) / "files/media").resolve()

CRISPY_TEMPLATE_PACK = "semantic-ui"
CRISPY_ALLOWED_TEMPLATE_PACKS = ("uni_form", "bootstrap4", "semantic-ui")

CONTENT_TYPE_EXCEL = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

CKEDITOR_BASEPATH = "/static/ckeditor/ckeditor/"

CKEDITOR_CONFIGS = {
    "default": {"toolbar": "basic", "height": 374, "width": 688},
    "basic_ckeditor": {"toolbar": "Basic"},
}
