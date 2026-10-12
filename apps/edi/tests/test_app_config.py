"""Tests de la configuration de l'app edi et de l'import de ses paquets vides"""

import importlib

import pytest
from django.apps import apps


def test_app_config():
    config = apps.get_app_config("edi")

    assert config.name == "apps.edi"
    assert config.default_auto_field == "django.db.models.BigAutoField"


@pytest.mark.parametrize(
    "module",
    [
        "apps.edi.admin",
        "apps.edi.essais",
        "apps.edi.data_fixtures",
        "apps.edi.excel_outputs",
        "apps.edi.exports",
        "apps.edi.forms.forms_pydantic",
        "apps.edi.forms.forms_serializers",
    ],
)
def test_packages_import(module):
    assert importlib.import_module(module)
