# pylint: disable=E0401,W0621
"""
FR : Tests de la configuration de l'app book (apps.py, urls, admin, packages)
EN : Tests for book app configuration

created at: 2026-10-11
created by: Paulo ALVES
"""
import importlib
from pathlib import Path

import pytest
from django.apps import apps as django_apps
from django.contrib import admin
from django.db.models import BigAutoField

import apps.book as book_package
from apps.book import forms as book_forms
from apps.book import models as book_models
from apps.book import urls as book_urls
from apps.book import views as book_views
from apps.book.apps import SuppliersBookConfig
from apps.book.models import base_sage_models, supplier_identifiers_models


def test_app_config():
    """L'app est enregistrée sous le label book avec des BigAutoField"""
    config = django_apps.get_app_config("book")

    assert isinstance(config, SuppliersBookConfig)
    assert config.name == "apps.book"
    assert SuppliersBookConfig.default_auto_field == "django.db.models.BigAutoField"
    assert isinstance(base_sage_models.Society._meta.pk, BigAutoField)  # pylint: disable=W0212


def test_package_init_vide():
    """Le __init__ de l'app ne porte plus de données de formulaire collées"""
    assert Path(book_package.__file__).read_text(encoding="utf8") == ""


def test_admin_vide():
    """Aucun modèle de book n'est enregistré dans l'admin"""
    assert not any(model._meta.app_label == "book" for model in admin.site._registry)  # pylint: disable=W0212


def test_models_package_reexporte_tous_les_modeles():
    """apps.book.models expose les modèles des deux sous-modules"""
    assert book_models.Society is base_sage_models.Society
    assert book_models.SupplierCct is supplier_identifiers_models.SupplierCct
    assert {model.__name__ for model in django_apps.get_app_config("book").get_models()} == {
        "Society",
        "Address",
        "Contact",
        "SocietyBank",
        "StatFamillyAxes",
        "SupplierFamilyAxes",
        "SupplierCct",
    }


def test_forms_et_views_reexportes():
    """Les packages forms et views exposent les classes des sous-modules"""
    assert book_forms.SocietyForm.Meta.model is book_models.Society
    assert book_forms.SageEmailForm().fields.keys() == {"email"}
    assert book_views.SocietiesList.model is book_models.Society


def test_routes_du_module():
    """Les 16 routes de l'app sont nommées et dans l'espace de noms book"""
    names = [pattern.name for pattern in book_urls.urlpatterns]

    assert book_urls.app_name == "apps.book"
    assert len(names) == 16
    assert len(set(names)) == 16
    assert {"societies_list", "supplier_cct_identifier", "statistique_update", "delete_familly_axes"} <= set(names)


@pytest.mark.parametrize(
    "module_name",
    [
        "apps.book.loggers",
        "apps.book.essais",
        "apps.book.exports",
        "apps.book.parameters",
        "apps.book.serializers",
        "apps.book.sql_files",
        "apps.book.tasks",
        "apps.book.templates",
        "apps.book.templates.book",
        "apps.book.validations",
        "apps.book.data_fixtures",
        "apps.book.excel_outputs",
        "apps.book.forms.forms_serializers",
        "apps.book.bin",
    ],
)
def test_packages_importables(module_name):
    """Les packages vides de l'app restent importables"""
    assert importlib.import_module(module_name) is not None
