# pylint: disable=E0401,W0621
"""
FR : Tests de la configuration de l'app core (apps.py, urls, admin, packages, vues api)
EN : Tests for core app configuration

created at: 2026-10-11
created by: Paulo ALVES
"""
import importlib
import logging

import pytest
from django.apps import apps as django_apps
from django.contrib import admin
from django.db.models import BigAutoField
from django.urls import reverse

from apps.core import urls as core_urls
from apps.core.apps import CoreConfig
from apps.core.models import ChangesTrace, Notification, PicklerFiles, SSEProgress
from apps.core.views import views as core_views

pytestmark = pytest.mark.django_db


def test_app_config():
    config = django_apps.get_app_config("core")

    assert isinstance(config, CoreConfig)
    assert config.name == "apps.core"
    assert CoreConfig.default_auto_field == "django.db.models.BigAutoField"
    assert isinstance(ChangesTrace._meta.pk, BigAutoField)  # pylint: disable=W0212


def test_admin_vide():
    assert not any(model._meta.app_label == "core" for model in admin.site._registry)  # pylint: disable=W0212


def test_modeles_de_l_app():
    assert {model.__name__ for model in django_apps.get_app_config("core").get_models()} == {
        "PicklerFiles",
        "ChangesTrace",
        "SSEProgress",
        "Notification",
    }
    assert PicklerFiles._meta.get_field("pickle_file").upload_to == "pickler/"  # pylint: disable=W0212
    assert Notification._meta.pk.name == "uuid_identification"  # pylint: disable=W0212
    assert SSEProgress._meta.get_field("job_id").unique is True  # pylint: disable=W0212


def test_routes_du_module():
    """10 routes nommées dans l'espace de noms core, sans la vue pdf de test"""
    names = [pattern.name for pattern in core_urls.urlpatterns]

    assert names == [
        "api_models_query",
        "api_models_query_third_party_num",
        "list_jobs",
        "active_jobs",
        "job_detail",
        "delete_job",
        "notifications_list",
        "notification_mark_read",
        "notification_mark_all_read",
        "notification_delete",
    ]
    assert reverse("core:list_jobs") == "/core/sse-progress/"


@pytest.mark.parametrize(
    "module_name",
    [
        "apps.core.bin",
        "apps.core.data_fixtures",
        "apps.core.exports",
        "apps.core.forms",
        "apps.core.forms.forms_django",
        "apps.core.forms.forms_djantic",
        "apps.core.forms.forms_pydantic",
        "apps.core.forms.forms_serializers",
        "apps.core.imports",
        "apps.core.invoices_clients_export",
        "apps.core.invoices_suppliers_export",
        "apps.core.invoices_suppliers_import",
        "apps.core.loops",
        "apps.core.modules",
        "apps.core.parameters",
        "apps.core.snippets",
        "apps.core.tasks",
        "apps.core.templates",
        "apps.core.templates.core",
        "apps.core.management",
        "apps.core.management.commands",
        "apps.core.utils",
        "apps.core.validations",
        "apps.core.excel_outputs",
        "apps.core.functions",
    ],
)
def test_packages_importables(module_name):
    assert importlib.import_module(module_name) is not None


def test_api_models_query_erreur_journalisee(ajax_client, monkeypatch, caplog):
    """Une fonction d'api qui lève une exception renvoie ko et journalise l'erreur"""

    def _boom(_query):
        raise RuntimeError("api cassée")

    monkeypatch.setitem(core_views.MODEL_DICT, "vats", _boom)

    with caplog.at_level(logging.ERROR):
        response = ajax_client.get(reverse("core:api_models_query", args=["vats", "x"]))

    assert response.json() == {"success": "ko"}
    assert "article_rest_api_query" in caplog.text
    assert "api cassée" in caplog.text
