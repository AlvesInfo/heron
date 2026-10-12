"""FR : Settings dédiés aux tests pytest.

EN : Settings dedicated to pytest tests.

Commentaire:

La base de données applicative passe par pgbouncer (10.9.2.109:6432) qui n'autorise pas la
création de la base "test_heron". Les tests utilisent donc le PostgreSQL local (localhost:5432).
Les alias secondaires ("heron", "formation", "bi_bdd") sont des miroirs de "default" afin que
Django ne tente pas de créer une base de test sur un serveur distant.

created at: 2026-10-10
created by: Paulo ALVES
"""

from decouple import AutoConfig

from heron import settings as _base_settings

# Ré-export des settings du module de base, sans import *
globals().update({name: value for name, value in vars(_base_settings).items() if name.isupper()})
from heron.settings import ENV_ROOT, LOGGING

_config = AutoConfig(search_path=ENV_ROOT)

_TEST_DATABASE = {
    "ENGINE": "django.db.backends.postgresql_psycopg2",
    "NAME": _config("TEST_NAME_DATABASE", default="heron"),
    "USER": _config("TEST_USER_DATABASE", default="paulo"),
    "PASSWORD": _config("TEST_PASSWORD_DATABASE", default=""),
    "HOST": _config("TEST_HOST_DATABASE", default="localhost"),
    "PORT": _config("TEST_PORT_DATABASE", default="5432"),
    "CONN_MAX_AGE": 0,
    "TEST": {"NAME": _config("TEST_DB_NAME", default="test_heron_pytest")},
}

DATABASES = {
    "default": _TEST_DATABASE,
    "heron": {**_TEST_DATABASE, "TEST": {"MIRROR": "default"}},
    "formation": {**_TEST_DATABASE, "TEST": {"MIRROR": "default"}},
    "bi_bdd": {**_TEST_DATABASE, "TEST": {"MIRROR": "default"}},
}

# Pas d'écriture de fichiers de logs pendant les tests : tout part sur la console
_logging: dict = LOGGING

for _handler in _logging["handlers"].values():
    if _handler.get("class") == "logging.FileHandler":
        _handler.update({"class": "logging.StreamHandler"})
        _handler.pop("filename", None)

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
