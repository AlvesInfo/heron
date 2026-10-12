# pylint: disable=E0401
"""
FR : Tests de la configuration de l'app groups (squelette sans modèle, vue ni route pour l'instant)
EN : Tests for groups app configuration (empty skeleton for now)

created at: 2026-10-11
created by: Paulo ALVES
"""
import importlib

import pytest
from django.apps import apps as django_apps
from django.contrib import admin

from apps.groups import urls as groups_urls
from apps.groups.apps import GroupsConfig


def test_app_config():
    """L'app est enregistrée et routée, sans modèle, route ni enregistrement admin"""
    config = django_apps.get_app_config("groups")

    assert isinstance(config, GroupsConfig)
    assert config.name == "apps.groups"
    assert GroupsConfig.default_auto_field == "django.db.models.BigAutoField"
    assert list(config.get_models()) == []
    assert groups_urls.urlpatterns == []
    assert not any(model._meta.app_label == "groups" for model in admin.site._registry)  # pylint: disable=W0212


@pytest.mark.parametrize(
    "module_name",
    [
        "apps.groups.models", "apps.groups.views", "apps.groups.admin", "apps.groups.bin", "apps.groups.data_fixtures",
        "apps.groups.essais", "apps.groups.excel_outputs", "apps.groups.exports", "apps.groups.forms",
        "apps.groups.forms.forms_django", "apps.groups.forms.forms_djantic", "apps.groups.forms.forms_pydantic",
        "apps.groups.forms.forms_serializers", "apps.groups.imports", "apps.groups.loops", "apps.groups.parameters",
        "apps.groups.tasks", "apps.groups.templates", "apps.groups.templates.groups", "apps.groups.validations",
    ],
)
def test_packages_importables(module_name):
    assert importlib.import_module(module_name) is not None
