# pylint: disable=E0401
"""FR : Tests de la configuration de l'app formations (squelette sans modèle ni vue pour l'instant)


EN : Tests for formations app configuration (empty skeleton for now)

created at: 2026-10-11
created by: Paulo ALVES
"""

import importlib

import pytest
from django.apps import apps as django_apps
from django.contrib import admin

from apps.formations.apps import FormationsConfig


def test_app_config():
    """L'app est enregistrée, sans modèle ni enregistrement admin"""
    config = django_apps.get_app_config("formations")

    assert isinstance(config, FormationsConfig)
    assert config.name == "apps.formations"
    assert FormationsConfig.default_auto_field == "django.db.models.BigAutoField"
    assert list(config.get_models()) == []
    assert not any(model._meta.app_label == "formations" for model in admin.site._registry)  # pylint: disable=W0212


@pytest.mark.parametrize(
    "module_name",
    [
        "apps.formations.models",
        "apps.formations.views",
        "apps.formations.admin",
        "apps.formations.bin",
        "apps.formations.data_fixtures",
        "apps.formations.essais",
        "apps.formations.excel_outputs",
        "apps.formations.exports",
        "apps.formations.forms",
        "apps.formations.forms.forms_django",
        "apps.formations.forms.forms_djantic",
        "apps.formations.forms.forms_pydantic",
        "apps.formations.forms.forms_serializers",
        "apps.formations.imports",
        "apps.formations.loops",
        "apps.formations.parameters",
        "apps.formations.tasks",
        "apps.formations.templates",
        "apps.formations.templates.formations",
        "apps.formations.validations",
    ],
)
def test_packages_importables(module_name):
    assert importlib.import_module(module_name) is not None
