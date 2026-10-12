# pylint: disable=E0401,W0621,W0212
"""
FR : Tests de la configuration et des modèles de l'app countries
EN : Tests for countries app configuration and models

created at: 2026-10-11
created by: Paulo ALVES
"""
import datetime
import importlib

import pytest
from django.apps import apps as django_apps
from django.contrib import admin
from django.db import IntegrityError, transaction

from apps.countries import urls as countries_urls
from apps.countries.apps import CountriesConfig
from apps.countries.models import (
    Country,
    Currency,
    ExchangeRate,
    Language,
    ValidationIntraVies,
    ValidationPostalCode,
)

pytestmark = pytest.mark.django_db


def test_app_config():
    config = django_apps.get_app_config("countries")

    assert isinstance(config, CountriesConfig)
    assert config.name == "apps.countries"
    assert CountriesConfig.default_auto_field == "django.db.models.BigAutoField"
    assert countries_urls.urlpatterns == []
    assert not any(model._meta.app_label == "countries" for model in admin.site._registry)
    assert {model.__name__ for model in config.get_models()} == {
        "Country", "Language", "Currency", "ExchangeRate", "ValidationPostalCode", "ValidationIntraVies",
    }


@pytest.mark.parametrize(
    "module_name",
    [
        "apps.countries.views", "apps.countries.essais", "apps.countries.excel_outputs", "apps.countries.exports",
        "apps.countries.parameters", "apps.countries.tasks", "apps.countries.templates", "apps.countries.templates.countries",
        "apps.countries.validations", "apps.countries.forms.forms_django", "apps.countries.forms.forms_pydantic",
        "apps.countries.forms.forms_serializers",
    ],
)
def test_packages_importables(module_name):
    assert importlib.import_module(module_name) is not None


def test_country_str_tri_et_import_sage(make_country):
    """Pays trié par nom ; métadonnées du fichier Sage ZBICRY (17 colonnes contiguës, clé country)"""
    make_country("FR", "France")
    make_country("DE", "Allemagne")

    assert str(Country.objects.get(pk="FR")) == "France"
    assert [country.country for country in Country.objects.all()] == ["DE", "FR"]
    assert Country.file_import_sage() == "ZBICRY_journalier.heron"
    assert Country.get_uniques() == {"country"}
    columns = Country.get_columns_import()
    assert list(columns.values()) == list(range(17))
    assert set(columns) <= {field.name for field in Country._meta.fields}
    assert Country().get_import == "methode d'import à retourner"
    assert Country.objects.get(pk="FR").cee is False


def test_langue_et_devise(make_language, make_country_currency):
    """Langues et devises : clé = code, devises triées par rang puis code"""
    make_language("FRA", "Français")
    make_country_currency("USD", "Dollar")
    euro = make_country_currency("EUR", "Euro")
    euro.ranking = 0
    euro.save()

    assert str(Language.objects.get(pk="FRA")) == "Français"
    assert [currency.code for currency in Currency.objects.all()] == ["EUR", "USD"]
    assert str(euro) == "EUR"


def test_taux_de_change_unique_par_jour():
    rate = ExchangeRate.objects.create(currency_iso_current="EUR", currency_iso_change="USD", average_exchange_rate="1.08")

    assert str(rate) == "EUR - USD"
    assert rate.exchange_date == datetime.date.today()
    assert rate.purchase_exchange_rate is None

    with pytest.raises(IntegrityError), transaction.atomic():
        ExchangeRate.objects.create(currency_iso_current="EUR", currency_iso_change="USD")


def test_validations_codes_postaux_et_tva_intra(make_country):
    """Une règle par pays pour les codes postaux et pour la tva intracommunautaire"""
    france = make_country("FR", "France")
    postal = ValidationPostalCode.objects.create(country=france, number_char=5, rule_number=1, exemple="75001")
    vies = ValidationIntraVies.objects.create(country=france, prefix="FR", func_verif="luhn", lng_min=11, lng_max=11)

    assert str(postal) == "France - 5 - 75001"
    assert str(vies) == "France - luhn"
    assert france.post_code_country == postal
    assert france.vies_country == vies

    with pytest.raises(IntegrityError), transaction.atomic():
        ValidationPostalCode.objects.create(country=france)
