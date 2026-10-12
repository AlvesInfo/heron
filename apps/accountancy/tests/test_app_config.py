# pylint: disable=E0401,W0621
"""FR : Tests de la configuration de l'app accountancy (apps.py, urls, admin, packages)


EN : Tests for accountancy app configuration

created at: 2026-10-10
created by: Paulo ALVES
"""

import importlib

import pytest
from django.apps import apps as django_apps
from django.contrib import admin
from django.db.models import BigAutoField

from apps.accountancy import models as accountancy_models, urls as accountancy_urls
from apps.accountancy.apps import AccountancyConfig
from apps.accountancy.models import pieces, sage, sage_axes_sections


def test_app_config():
    """L'app est enregistrée sous le label accountancy avec des BigAutoField"""
    config = django_apps.get_app_config("accountancy")

    assert isinstance(config, AccountancyConfig)
    assert config.name == "apps.accountancy"
    assert AccountancyConfig.default_auto_field == "django.db.models.BigAutoField"
    assert isinstance(sage.AccountSage._meta.pk, BigAutoField)  # pylint: disable=W0212


def test_urls_et_admin_vides():
    """Pas de route ni d'enregistrement admin pour l'instant"""
    assert accountancy_urls.urlpatterns == []
    assert not any(model._meta.app_label == "accountancy" for model in admin.site._registry)  # pylint: disable=W0212


def test_models_package_reexporte_tous_les_modeles():
    """apps.accountancy.models expose les modèles des trois sous-modules"""
    assert accountancy_models.AxeSage is sage_axes_sections.AxeSage
    assert accountancy_models.VatSage is sage.VatSage
    assert accountancy_models.Ecritures is pieces.Ecritures
    assert {model.__name__ for model in django_apps.get_app_config("accountancy").get_models()} == {
        "AxeSage",
        "SectionSage",
        "AccountSage",
        "CctSage",
        "VatRegimeSage",
        "VatSage",
        "VatRatSage",
        "ModeReglement",
        "PaymentCondition",
        "TabDivSage",
        "CategorySage",
        "CurrencySage",
        "CodePlanSage",
        "Pieces",
        "Journaux",
        "Transactions",
        "Ecritures",
    }


@pytest.mark.parametrize(
    "module_name",
    [
        "apps.accountancy.loggers",
        "apps.accountancy.views",
        "apps.accountancy.tasks",
        "apps.accountancy.data_fixtures",
        "apps.accountancy.excel_outputs",
        "apps.accountancy.exports",
        "apps.accountancy.parameters",
        "apps.accountancy.snippets",
        "apps.accountancy.templates",
        "apps.accountancy.templates.accountancy",
        "apps.accountancy.forms.forms_pydantic",
        "apps.accountancy.forms.forms_serializers",
        "apps.accountancy.bin",
    ],
)
def test_packages_importables(module_name):
    """Les packages vides de l'app restent importables"""
    assert importlib.import_module(module_name) is not None
