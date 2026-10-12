# pylint: disable=E0401,W0621
"""
FR : Tests de la configuration de l'app articles
EN : Tests for articles app configuration

created at: 2026-10-10
created by: Paulo ALVES
"""
import importlib

import pytest
from django.contrib import admin
from django.apps import apps as django_apps

from apps.articles import urls as articles_urls
from apps.articles.apps import ArticlesConfig


def test_app_config():
    """App enregistrée avec BigAutoField"""
    config = django_apps.get_app_config("articles")

    assert isinstance(config, ArticlesConfig)
    assert config.name == "apps.articles"
    assert ArticlesConfig.default_auto_field == "django.db.models.BigAutoField"


def test_routes():
    """18 routes nommées"""
    names = {pattern.name for pattern in articles_urls.urlpatterns}

    assert articles_urls.app_name == "apps.articles"
    assert len(articles_urls.urlpatterns) == 18
    assert {"suppliers_articles_list", "articles_list", "article_create", "article_update", "articles_export_list", "articles_search_list"} <= names
    assert {"articles_account_vat_create", "delete_articles_account_vat", "new_articles_list", "articles_new_validation", "articles_news_export_list"} <= names
    assert {"articles_without_account_list", "articles_without_account_export_list", "update_articles_without_account"} <= names
    assert {"articles_account_list", "articles_account_update", "articles_account_supplier_export", "update_articles_accounts_file"} <= names


def test_admin_vide():
    """Aucun modèle de l'app dans l'admin"""
    assert not any(model._meta.app_label == "articles" for model in admin.site._registry)  # pylint: disable=W0212


@pytest.mark.parametrize(
    "module_name",
    [
        "apps.articles.bin", "apps.articles.data_fixtures", "apps.articles.essais", "apps.articles.excel_outputs",
        "apps.articles.exports", "apps.articles.forms.forms_pydantic", "apps.articles.forms.forms_serializers",
        "apps.articles.imports", "apps.articles.loops", "apps.articles.parameters", "apps.articles.sql",
        "apps.articles.tasks", "apps.articles.templates", "apps.articles.templates.articles", "apps.articles.validations",
        "apps.articles.data_fixtures.familles_stat_fixtures",
    ],
)
def test_packages_importables(module_name):
    """Les packages vides et le script de fixtures commenté restent importables"""
    assert importlib.import_module(module_name) is not None
