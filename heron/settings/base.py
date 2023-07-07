# pylint: disable=E0401
"""
Django settings for heron project.
"""
import sys
from pathlib import Path

from decouple import Csv, AutoConfig
from django.utils.translation import gettext_lazy as _
from sqlalchemy import create_engine, MetaData
from sqlalchemy.pool import NullPool

BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_DIR = Path(__file__).resolve().parent.parent
APPS_DIR = (Path(BASE_DIR) / "apps").resolve()
CORE_DIR = (Path(APPS_DIR) / "core").resolve()

sys.path.append(str(BASE_DIR))
sys.path.append(str(PROJECT_DIR))
sys.path.append(str(APPS_DIR))
sys.path.append(str(CORE_DIR))

path_env = (Path(PROJECT_DIR) / "env/.env").resolve()

config = AutoConfig(search_path=path_env)

SECRET_KEY = config("SECRET_KEY")
ENV_ROOT = path_env

EMAIL_HOST = config("EMAIL_HOST", default="localhost")
EMAIL_PORT = config("EMAIL_PORT", default=25, cast=int)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="comptabilite@acuitis.com")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default=None)
EMAIL_USE_SSL = config("EMAIL_USE_SSL", default=True, cast=bool)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=False, cast=bool)
DKIM_PEM_FILE = config("DKIM_PEM_FILE", default="")

EMAIL_DEV = config("EMAIL_HOST_USER", default="comptabilite@acuitis.com")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="comptabilite@acuitis.com")

NAME_DATABASE = config("NAME_DATABASE")
USER_DATABASE = config("USER_DATABASE")
PASSWORD_DATABASE = config("PASSWORD_DATABASE")
HOST_DATABASE = config("HOST_DATABASE")
HOST_DATABASE_HERON = config("HOST_DATABASE_HERON")
PORT_DATABASE = config("PORT_DATABASE")
PORT_DATABASE_HERON = config("PORT_DATABASE_HERON", default=PORT_DATABASE)

# CNX_STRING pour le pool de connexion
CNX_STRING = (
    f"dbname={NAME_DATABASE} "
    f"user={USER_DATABASE} "
    f"password={PASSWORD_DATABASE} "
    f"host={HOST_DATABASE} "
    f"port={PORT_DATABASE}"
)

NAME_DATABASE_BI = config("NAME_DATABASE_BI")
USER_DATABASE_BI = config("USER_DATABASE_BI")
PASSWORD_DATABASE_BI = config("PASSWORD_DATABASE_BI")
HOST_DATABASE_BI = config("HOST_DATABASE_BI")
PORT_DATABASE_BI = config("PORT_DATABASE_BI")

REDIS_HOST = config("REDIS_HOST")
REDIS_PORT = config("REDIS_PORT")
REDIS_PASSWORD = config("REDIS_PASSWORD")

ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv())

WHITELIST = config("ALLOWED_HOSTS", cast=Csv())

DOMAIN = config("DOMAIN", default="acuitis.com")

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# REPERTOIRE DES LOGS
LOG_DIR = (
    (Path(BASE_DIR) / config("LOG_BASE_PATH", default=None)).resolve()
    if config("LOG_BASE_PATH", default=None) is not None
    else Path("/var/log/heron").resolve()
)
Path.mkdir(LOG_DIR, exist_ok=True)

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
    "rest_framework",
    "rest_framework.authtoken",
    "django_filters",
    "django_extensions",
    "crispy_forms",
    "crispy_forms_semantic_ui",
    "axes",
    "ckeditor",
    "chartjs",
    "dynamic_preferences",
    # comment the following line if you don't want to use user preferences
    "dynamic_preferences.users.apps.UserPreferencesConfig",
    "django_celery_results",
    "django_celery_beat",
]

LOCAL_APPS = [
    "heron",
    "apps.accountancy",
    "apps.articles",
    "apps.book",
    "apps.centers_clients",
    "apps.centers_purchasing",
    "apps.compta",
    "apps.core",
    "apps.data_flux",
    "apps.countries",
    "apps.edi",
    "apps.formations",
    "apps.groups",
    "apps.import_files",
    "apps.invoices",
    "apps.parameters",
    "apps.periods",
    "apps.permissions",
    "apps.rfa",
    "apps.traces",
    "apps.users",
    "apps.validation_purchases",
    "apps.validation_sales",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "heron.middleware.login_middleware.LoginMiddleware",
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
            Path(BASE_DIR)
            / "apps/data_flux/templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "dynamic_preferences.processors.global_preferences",
                "heron.processors.title",
                "heron.processors.user_group",
                "heron.processors.groups_processor",
                "heron.processors.groupes_processor",
                "heron.processors.date_du_jour",
                "heron.processors.annee_du_jour",
                "heron.processors.debug",
                "heron.processors.domain_site",
                "heron.processors.domain_debug",
                "heron.processors.user_paulo",
                "heron.processors.in_acuitis",
                "heron.processors.in_ari",
                "heron.processors.in_do",
                "heron.processors.in_ga",
                "heron.processors.in_maa",
                "heron.processors.in_unisson",
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
        'OPTIONS': {
             'sslmode': 'disable',
         },
    },
    "heron": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": NAME_DATABASE,
        "USER": USER_DATABASE,
        "PASSWORD": PASSWORD_DATABASE,
        "HOST": HOST_DATABASE_HERON,
        "PORT": PORT_DATABASE_HERON,
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
    # "axes.backends.AxesBackend",
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

LANGUAGE_CODE = "fr"
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


Path.mkdir(BASE_DIR / "files/static/css", exist_ok=True)
Path.mkdir(BASE_DIR / "files/static/js", exist_ok=True)
Path.mkdir(BASE_DIR / "files/static/img", exist_ok=True)
Path.mkdir(BASE_DIR / "files/static/images", exist_ok=True)
Path.mkdir(BASE_DIR / "files/static/fonts", exist_ok=True)
Path.mkdir(BASE_DIR / "files/static/vendor", exist_ok=True)

STATICFILES_DIRS = [
    (Path(BASE_DIR) / "files/static/css").resolve(),
    (Path(BASE_DIR) / "files/static/js").resolve(),
    (Path(BASE_DIR) / "files/static/img").resolve(),
    (Path(BASE_DIR) / "files/static/images").resolve(),
    (Path(BASE_DIR) / "files/static/fonts").resolve(),
    (Path(BASE_DIR) / "files/static/vendor").resolve(),
]

MEDIA_URL = "/media/"
MEDIA_ROOT = (Path(BASE_DIR) / "files/media").resolve()

CRISPY_TEMPLATE_PACK = "semantic-ui"
CRISPY_ALLOWED_TEMPLATE_PACKS = ("uni_form", "bootstrap4", "semantic-ui")

CONTENT_TYPE_EXCEL = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

CKEDITOR_BASEPATH = "/static/ckeditor/ckeditor/"

CKEDITOR_CONFIGS = {
    "default": {"toolbar": "basic", "height": 374, "width": 688},
    "basic_ckeditor": {"toolbar": "Basic"},
}

# available settings with their default values
DYNAMIC_PREFERENCES = {
    "MANAGER_ATTRIBUTE": "preferences",
    "ENABLE_GLOBAL_MODEL_AUTO_REGISTRATION": True,
    "ENABLE_CACHE": True,
    "CACHE_NAME": "default",
    "VALIDATE_NAMES": True,
}

engine = create_engine(
    f"postgresql+psycopg2://"
    f"{USER_DATABASE}:{USER_DATABASE}"
    f"@"
    f"{HOST_DATABASE}:{PORT_DATABASE}"
    f"/"
    f"{NAME_DATABASE}",
    future=True,
    poolclass=NullPool,
)

meta_data_heron = MetaData()

with engine.connect() as connection:
    meta_data_heron.reflect(connection)

TraceError = meta_data_heron.tables["data_flux_error"]
TraceLine = meta_data_heron.tables["data_flux_line"]
Trace = meta_data_heron.tables["data_flux_trace"]
EdiImport = meta_data_heron.tables["edi_ediimport"]
EdiSupplier = meta_data_heron.tables["edi_supplierdefinition"]
EdiColumns = meta_data_heron.tables["edi_columndefinition"]


CELERY_RESULT_BACKEND = "django-db"
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
# CELERY_TASK_TIME_LIMIT = 60 * 60
