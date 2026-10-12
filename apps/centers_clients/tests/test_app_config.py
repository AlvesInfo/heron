# pylint: disable=E0401,W0621
"""
FR : Tests de la configuration de l'app centers_clients
EN : Tests for centers_clients app configuration

created at: 2026-10-10
created by: Paulo ALVES
"""
import importlib

import pytest
from django.contrib import admin
from django.apps import apps as django_apps

from apps.centers_clients import urls as cc_urls
from apps.centers_clients.apps import CentersClientsConfig


def test_app_config():
    """App enregistrée avec BigAutoField"""
    config = django_apps.get_app_config("centers_clients")

    assert isinstance(config, CentersClientsConfig)
    assert config.name == "apps.centers_clients"
    assert CentersClientsConfig.default_auto_field == "django.db.models.BigAutoField"


def test_routes():
    """27 routes nommées, réparties par écran"""
    names = {pattern.name for pattern in cc_urls.urlpatterns}

    assert cc_urls.app_name == "apps.centers_clients"
    assert len(cc_urls.urlpatterns) == 27
    assert {"maisons_list", "import_bi", "maisons_create", "maisons_update", "maisons_export_list"} <= names
    assert {"exclusions_list", "exclusion_create", "exclusion_update", "exclusion_delete", "exclusion_export_list"} <= names
    assert {"exclusions_country_list", "exclusion_country_delete", "exclusion_country_export_list"} <= names
    assert {"client_familly_list", "client_familly_create", "client_familly_update", "client_familly_delete"} <= names
    assert {"subscriptions_list", "subscription_create", "subscription_update", "subscription_delete", "insert_or_update_subscriptions"} <= names


def test_admin_vide():
    """Aucun modèle de l'app enregistré dans l'admin"""
    assert not any(model._meta.app_label == "centers_clients" for model in admin.site._registry)  # pylint: disable=W0212


@pytest.mark.parametrize(
    "module_name",
    [
        "apps.centers_clients.bin", "apps.centers_clients.data_fixtures", "apps.centers_clients.essais",
        "apps.centers_clients.excel_outputs", "apps.centers_clients.exports", "apps.centers_clients.forms.forms_pydantic",
        "apps.centers_clients.forms.forms_serializers", "apps.centers_clients.imports", "apps.centers_clients.loops",
        "apps.centers_clients.parameters", "apps.centers_clients.sql", "apps.centers_clients.tasks",
        "apps.centers_clients.templates", "apps.centers_clients.templates.centers_clients", "apps.centers_clients.validations",
    ],
)
def test_packages_importables(module_name):
    """Les packages vides restent importables"""
    assert importlib.import_module(module_name) is not None
