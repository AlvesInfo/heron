# pylint: disable=E0401,W0621
"""FR : Tests de l'app periods (formulaire de mois, modèle Periode, fixtures)


EN : Tests for periods app

created at: 2026-10-12
created by: Paulo ALVES
"""

import datetime
import importlib

import pendulum
import pytest
from django.apps import apps as django_apps
from django.db.utils import IntegrityError

from apps.periods import urls as periods_urls
from apps.periods.apps import PeriodsConfig
from apps.periods.data_fixtures.insert_fixtures import fixtures_periodes
from apps.periods.forms import (
    MonthForm,
    YearForm,
    YearPassedForm,
    get_month_choices,
    get_year_choices,
    get_year_passed_choices,
)
from apps.periods.models import Periode


def test_app_config_et_routes():
    config = django_apps.get_app_config("periods")

    assert isinstance(config, PeriodsConfig)
    assert config.name == "apps.periods"
    assert periods_urls.urlpatterns == []
    assert importlib.import_module("apps.periods.admin") is not None
    assert importlib.import_module("apps.periods.views") is not None


def test_choix_des_mois():
    """25 mois de M-12 à M+12, valeur début_fin du mois, initial au mois précédent"""
    choices = get_month_choices()
    now = pendulum.now()
    previous = now.subtract(months=1)
    expected_initial = f"{previous.start_of('month').date().isoformat()}_{previous.end_of('month').date().isoformat()}"

    assert len(choices["periods"]) == 25
    assert choices["periods"][0][0].startswith(
        now.subtract(months=12).start_of("month").date().isoformat()
    )
    assert choices["initial"][0] == expected_initial
    assert choices["initial"][1] == previous.format("MMMM YYYY", locale="fr").capitalize()


def test_formulaire_de_mois():
    choices = get_month_choices()
    valid = MonthForm({"periode": choices["initial"][0]})
    invalid = MonthForm({"periode": "2000-01-01_2000-01-31"})
    empty = MonthForm({})

    assert valid.fields["periode"].initial == choices["initial"]
    assert len(valid.fields["periode"].choices) == 25
    assert valid.is_valid()
    assert invalid.is_valid() is False
    assert empty.is_valid() is False


def test_choix_des_annees():
    """21 années de Y-10 à Y+10, valeur = année, initial = année en cours"""
    choices = get_year_choices()
    year = pendulum.now().year

    assert len(choices["periods"]) == 21
    assert choices["periods"][0] == (str(year - 10), f"Année {year - 10}")
    assert choices["periods"][-1] == (str(year + 10), f"Année {year + 10}")
    assert choices["initial"] == (str(year), f"Année {year}")


def test_formulaire_d_annee():
    year = pendulum.now().year
    valid = YearForm({"periode": str(year)})
    invalid = YearForm({"periode": str(year + 11)})

    assert valid.fields["periode"].initial == (str(year), f"Année {year}")
    assert len(valid.fields["periode"].choices) == 21
    assert valid.is_valid()
    assert valid.cleaned_data["periode"] == str(year)
    assert invalid.is_valid() is False
    assert YearForm({}).is_valid() is False


@pytest.mark.django_db
def test_annees_facturees_sans_facture():
    """Sans facture de vente : seule l'année en cours est proposée"""
    year = pendulum.now().year

    assert get_year_passed_choices() == {
        "initial": (str(year), f"Année {year}"),
        "periods": [(str(year), f"Année {year}")],
    }
    assert YearPassedForm({"periode": str(year)}).is_valid()
    assert YearPassedForm({"periode": str(year - 1)}).is_valid() is False


@pytest.mark.django_db
def test_annees_facturees_depuis_la_premiere_facture(make_sale_invoice):
    """De la première année de facture à l'année en cours, initiale = année en cours"""
    year = pendulum.now().year
    make_sale_invoice(invoice_year=year - 3)
    make_sale_invoice(invoice_year=year - 1)

    choices = get_year_passed_choices()
    form = YearPassedForm({"periode": str(year - 3)})

    assert [value for value, _ in choices["periods"]] == [str(y) for y in range(year - 3, year + 1)]
    assert choices["initial"] == (str(year), f"Année {year}")
    assert form.fields["periode"].initial == choices["initial"]
    assert form.is_valid()
    assert YearPassedForm({"periode": str(year - 4)}).is_valid() is False


@pytest.mark.django_db
def test_modele_periode():
    values = {
        "year": 2026,
        "period_type": "Mois",
        "wording": "Janvier 2026",
        "start_date": datetime.date(2026, 1, 1),
        "end_date": datetime.date(2026, 1, 31),
    }
    periode = Periode.objects.create(**values)

    assert str(periode) == "2026 - Mois - Janvier 2026"

    with pytest.raises(IntegrityError):
        Periode.objects.create(**values)


@pytest.mark.django_db
def test_fixtures_periodes(monkeypatch):
    """Le csv des périodes est chargé de façon idempotente, les doublons sont ignorés"""
    fixtures_periodes()
    count = Periode.objects.count()

    assert count > 700
    assert Periode.objects.filter(year=2011, period_type="Année").count() == 1
    assert Periode.objects.get(year=2011, wording="Janvier 2011").end_date == datetime.date(
        2011, 1, 31
    )

    fixtures_periodes()
    assert Periode.objects.count() == count

    def _raise(**_kwargs):
        raise IntegrityError("doublon")

    monkeypatch.setattr(Periode.objects, "update_or_create", _raise)
    fixtures_periodes()
    assert Periode.objects.count() == count
