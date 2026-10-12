"""Tests de la configuration de l'app compta et de ses paquets"""

import importlib

from django.apps import apps


def test_app_config():
    config = apps.get_app_config("compta")

    assert config.name == "apps.compta"
    assert type(config).__name__ == "ComptaConfig"


def test_paquets_importables():
    for name in [
        "apps.compta.forms",
        "apps.compta.tasks",
        "apps.compta.parameters",
        "apps.compta.validations",
        "apps.compta.essais",
        "apps.compta.data_fixtures",
        "apps.compta.exports",
        "apps.compta.admin",
        "apps.compta.excel_outputs.columns_excel",
    ]:
        assert importlib.import_module(name)
