# pylint: disable=E0401,W0621
"""FR : Tests de l'infrastructure du projet heron : tables abstraites, loggers, application celery,


     utilitaires de répertoires, commande init_directories, points d'entrée ASGI / WSGI
EN : Tests for heron project infrastructure

created at: 2026-10-12
created by: Paulo ALVES
"""

import asyncio
import io
import logging
import types
from pathlib import Path, PosixPath

import pytest
from django.conf import settings as django_settings
from django.core.management import call_command

import heron.settings
from heron import asgi, celery_app, loggers, wsgi
from heron.models import CreateTable, DatesTable, DbTableAuthorisation, FlagExport, FlagsTable
from heron.utils import directories

# MODÈLES ==========================================================================================


def test_tables_abstraites():
    assert all(model._meta.abstract for model in (DatesTable, FlagsTable, FlagExport, CreateTable))
    assert {
        "active",
        "delete",
        "export",
        "valid",
        "created_by",
        "modified_by",
        "acquitted_by",
        "delete_by",
    } <= {field.name for field in FlagsTable._meta.fields}
    assert {"export", "final", "final_at", "created_by", "modified_by"} <= {
        field.name for field in FlagExport._meta.fields
    }
    assert {field.name for field in CreateTable._meta.fields} == {
        "created_at",
        "modified_at",
        "created_by",
    }


@pytest.mark.django_db
def test_table_des_autorisations(make_user):
    authorisation = DbTableAuthorisation.objects.create(
        user=make_user(), model_to_consult="book.Society"
    )

    assert (authorisation.all_table, authorisation.to_display, authorisation.to_edit) == (
        False,
        True,
        True,
    )


# LOGGERS ET CELERY ================================================================================


def test_loggers_nommes():
    expected = {
        "LOGGER_IMPORT": "imports",
        "LOGGER_EXPORT_EXCEL": "export_excel",
        "LOGGER_VIEWS": "error_views",
        "LOGGER_DJANGO": "django",
        "LOGGER_PRODUCTION": "production",
        "LOGGER_CONNEXION": "connexion",
        "LOGGER_TIMER_HERON": "timer_heron",
        "LOGGER_EDI": "edi",
        "LOGGER_LOADER": "loader",
        "LOGGER_VALIDATION": "validation",
        "LOGGER_POSTGRES_SAVE": "postgres_save",
        "LOGGER_INVOICES": "invoices_flux",
        "LOGGER_EMAIL": "send_email",
        "LOGGER_X3": "export_x3",
    }

    for attribute, name in expected.items():
        logger = getattr(loggers, attribute)
        assert isinstance(logger, logging.Logger)
        assert logger.name == name


def test_application_celery():
    assert celery_app.main == "heron"
    assert django_settings.REDIS_HOST in celery_app.conf.broker_url
    assert celery_app.conf.task_acks_late is True
    assert celery_app.conf.worker_prefetch_multiplier == 1


# RÉPERTOIRES ======================================================================================


def test_creation_paresseuse_des_repertoires(tmp_path, monkeypatch):
    """ensure_directory crée une seule fois (cache), lazy_mkdir ne crée rien"""
    monkeypatch.setattr(directories, "_initialized_dirs", set())
    target = tmp_path / "a" / "b"

    assert directories.ensure_directory(target) == target
    assert target.is_dir()

    target.rmdir()
    assert directories.ensure_directory(target) == target
    assert not target.exists()

    lazy = directories.lazy_mkdir("files/repertoire_de_test_inexistant")
    assert (
        lazy == (directories.get_files_base_dir() / "files/repertoire_de_test_inexistant").resolve()
    )
    assert not lazy.exists()
    assert directories.get_files_base_dir() == Path(__file__).resolve().parent.parent.parent
    assert directories.get_files_base_dir() == django_settings.FILES_BASE_DIR


class _BoomPath(PosixPath):
    """Chemin dont le test d'existence échoue (branche d'erreur de la commande)"""

    def exists(self):
        raise OSError("disque indisponible")


def _run_init_directories(monkeypatch, settings, tmp_path, with_log_dir=True):
    monkeypatch.setattr(directories, "_initialized_dirs", set())
    monkeypatch.setattr(
        heron.settings,
        "directories",
        types.SimpleNamespace(
            NEW_DIR=tmp_path / "nouveau",
            EXISTING_DIR=tmp_path,
            FILES_BASE_DIR=tmp_path / "ignore_base",
            lower_dir=tmp_path / "ignore_minuscule",
            NOT_A_PATH="texte",
        ),
    )
    monkeypatch.setattr(
        heron.settings,
        "suppliers",
        types.SimpleNamespace(BOOM_DIR=_BoomPath(tmp_path / "boom"), NOT_A_PATH="texte"),
    )
    settings.STATICFILES_DIRS = [tmp_path / "static", "pas_un_path"]

    if with_log_dir:
        settings.LOG_DIR = tmp_path / "logs"
    else:
        del settings.LOG_DIR

    out = io.StringIO()
    call_command("init_directories", stdout=out)
    return out.getvalue()


@pytest.mark.django_db
def test_commande_init_directories(monkeypatch, settings, tmp_path):
    """Crée les répertoires manquants, ignore ceux qui existent, signale les erreurs"""
    output = _run_init_directories(monkeypatch, settings, tmp_path)

    assert (tmp_path / "nouveau").is_dir()
    assert (tmp_path / "logs").is_dir()
    assert (tmp_path / "static").is_dir()
    assert not (tmp_path / "ignore_base").exists()
    assert not (tmp_path / "ignore_minuscule").exists()
    assert "Créé: NEW_DIR" in output
    assert "Créé: LOG_DIR" in output
    assert "Créé: STATICFILES_DIR_0" in output
    assert "Erreur pour BOOM_DIR: disque indisponible" in output
    assert "3 répertoires créés" in output
    assert "1 répertoires existaient déjà" in output
    assert "Total: 4 répertoires" in output


@pytest.mark.django_db
def test_commande_init_directories_sans_log_dir(monkeypatch, settings, tmp_path):
    output = _run_init_directories(monkeypatch, settings, tmp_path, with_log_dir=False)

    assert "LOG_DIR" not in output
    assert "2 répertoires créés" in output


# POINTS D'ENTRÉE ==================================================================================


def test_wsgi():
    assert callable(wsgi.application)


def test_asgi_cycle_de_vie_et_requetes(monkeypatch):
    """Le protocole lifespan est acquitté (startup, shutdown), le reste est confié à Django"""
    sent = []
    messages = iter(
        [{"type": "lifespan.startup"}, {"type": "lifespan.autre"}, {"type": "lifespan.shutdown"}]
    )

    async def receive():
        return next(messages)

    async def send(message):
        sent.append(message)

    asyncio.run(asgi.application({"type": "lifespan"}, receive, send))
    assert sent == [{"type": "lifespan.startup.complete"}, {"type": "lifespan.shutdown.complete"}]

    handled = []

    async def fake_django(scope, _receive, _send):
        handled.append(scope["type"])

    monkeypatch.setattr(asgi, "django_asgi_app", fake_django)
    asyncio.run(asgi.application({"type": "http"}, receive, send))
    assert handled == ["http"]
