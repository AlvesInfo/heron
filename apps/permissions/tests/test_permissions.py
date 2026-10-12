# pylint: disable=E0401
"""
FR : Tests de l'app permissions (squelette : configuration et routes vides)
EN : Tests for permissions app skeleton

created at: 2026-10-12
created by: Paulo ALVES
"""
import importlib

from django.apps import apps as django_apps

from apps.permissions import urls as permissions_urls
from apps.permissions.apps import PermissionsConfig


def test_app_config_et_routes():
    config = django_apps.get_app_config("permissions")

    assert isinstance(config, PermissionsConfig)
    assert config.name == "apps.permissions"
    assert list(config.get_models()) == []
    assert permissions_urls.urlpatterns == []
    assert importlib.import_module("apps.permissions.admin") is not None
    assert importlib.import_module("apps.permissions.views") is not None
    assert importlib.import_module("apps.permissions.models") is not None
