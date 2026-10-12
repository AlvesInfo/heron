"""Tests de la configuration de l'app validation_purchases"""
import importlib

from django.apps import apps


def test_app_config():
    config = apps.get_app_config("validation_purchases")

    assert config.name == "apps.validation_purchases"
    assert type(config).__name__ == "ValidationPurchasesConfig"


def test_paquets_importables():
    for name in ["apps.validation_purchases", "apps.validation_purchases.admin", "apps.validation_purchases.models",
                 "apps.validation_purchases.forms", "apps.validation_purchases.urls", "apps.validation_purchases.views"]:
        assert importlib.import_module(name)


def test_init_vide():
    """Le paquet ne porte plus de données POST collées"""
    import apps.validation_purchases as package

    assert not hasattr(package, "base_date")
    assert not hasattr(package, "d")
