# pylint: disable=E0401,W0621
"""
FR : Tests de la configuration de l'app centers_purchasing (apps.py, urls, admin, packages)
EN : Tests for centers_purchasing app configuration

created at: 2026-10-11
created by: Paulo ALVES
"""
import importlib

import pytest
from django.apps import apps as django_apps
from django.contrib import admin
from django.db.models import BigAutoField

from apps.centers_purchasing import forms as cp_forms
from apps.centers_purchasing import models as cp_models
from apps.centers_purchasing import urls as cp_urls
from apps.centers_purchasing import views as cp_views
from apps.centers_purchasing.apps import CentersPurchasingConfig


def test_app_config():
    config = django_apps.get_app_config("centers_purchasing")

    assert isinstance(config, CentersPurchasingConfig)
    assert config.name == "apps.centers_purchasing"
    assert CentersPurchasingConfig.default_auto_field == "django.db.models.BigAutoField"
    assert isinstance(cp_models.Signboard._meta.pk, BigAutoField)  # pylint: disable=W0212


def test_admin_vide():
    assert not any(model._meta.app_label == "centers_purchasing" for model in admin.site._registry)  # pylint: disable=W0212


def test_modeles_de_l_app():
    assert {model.__name__ for model in django_apps.get_app_config("centers_purchasing").get_models()} == {
        "Action",
        "PrincipalCenterPurchase",
        "ChildCenterPurchase",
        "Signboard",
        "SignboardModel",
        "Translation",
        "SignboardModelTranslate",
        "TranslationParamaters",
        "GroupingGoods",
        "AxeProGroupingGoods",
        "AccountsAxeProCategory",
        "ApplicableProVat",
        "TypeFacture",
    }


def test_forms_et_views_reexportes():
    assert cp_forms.MeresForm.Meta.model is cp_models.PrincipalCenterPurchase
    assert cp_forms.AccountsAxeProCategoryForm.Meta.model is cp_models.AccountsAxeProCategory
    assert cp_views.MeresList.model is cp_models.PrincipalCenterPurchase
    assert cp_views.AccountAxeList.model is cp_models.AccountsAxeProCategory


def test_routes_du_module():
    """37 routes nommées, uniques, dans l'espace de noms centers_purchasing"""
    names = [pattern.name for pattern in cp_urls.urlpatterns]

    assert cp_urls.app_name == "apps.centers_purchasing"
    assert len(names) == 37
    assert len(set(names)) == 37
    assert {"meres_list", "fille_update", "enseigne_create", "type_facture_delete", "account_axe_import_file"} <= set(names)


@pytest.mark.parametrize(
    "module_name",
    [
        "apps.centers_purchasing.essais",
        "apps.centers_purchasing.exports",
        "apps.centers_purchasing.loops",
        "apps.centers_purchasing.parameters",
        "apps.centers_purchasing.tasks",
        "apps.centers_purchasing.templates",
        "apps.centers_purchasing.templates.centers_purchasing",
        "apps.centers_purchasing.validations",
        "apps.centers_purchasing.sql_files",
        "apps.centers_purchasing.data_fixtures",
        "apps.centers_purchasing.imports",
        "apps.centers_purchasing.forms.forms_pydantic",
        "apps.centers_purchasing.forms.forms_serializers",
        "apps.centers_purchasing.views.invoices_accounts_views",
        "apps.centers_purchasing.bin",
    ],
)
def test_packages_importables(module_name):
    assert importlib.import_module(module_name) is not None


def test_sql_des_articles_sans_comptes_est_une_requete():
    from apps.centers_purchasing.sql_files.sql_elements import articles_acuitis_without_accounts  # pylint: disable=C0415

    assert articles_acuitis_without_accounts.strip().startswith("with")
    assert '"edi_ediimport"' in articles_acuitis_without_accounts
