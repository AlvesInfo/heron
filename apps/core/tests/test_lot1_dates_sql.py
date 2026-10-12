# pylint: disable=E0401,W0621
"""
FR : Tests des utilitaires de dates (functions_dates.py) et sql (functions_sql.py) de core
EN : Tests for core date and sql helpers

created at: 2026-10-11
created by: Paulo ALVES
"""
import datetime

import pytest

from apps.core.functions.functions_dates import (
    DATE_FORMATS,
    MONTHS,
    TRUNC_MONTHS,
    WEEK_DAYS_FR,
    WEEK_DAYS_SHORT_FR,
    date_string_series,
    days_of_month,
    get_date_apostrophe,
    last_day_month,
    long_date_string,
    time_string_series,
    validate_date,
)
from apps.core.functions.functions_sql import clean_id


# DATES ============================================================================================


def test_constantes_des_mois_et_jours():
    """13 entrées (index 0 vide) pour les mois, 7 jours de la semaine"""
    assert len(MONTHS) == len(TRUNC_MONTHS) == 13
    assert (MONTHS[1], MONTHS[12], TRUNC_MONTHS[2]) == ("janvier", "décembre", "févr.")
    assert len(WEEK_DAYS_FR) == len(WEEK_DAYS_SHORT_FR) == 7
    assert WEEK_DAYS_FR[0] == "lundi"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("", "de "),
        ("avril", "d'"),
        ("Octobre", "d'"),
        ("août", "d'"),
        ("mars", "de "),
        (datetime.date(2026, 4, 1), "d'"),
        (datetime.date(2026, 8, 1), "d'"),
        (datetime.date(2026, 10, 1), "d'"),
        (datetime.date(2026, 3, 1), "de "),
        (datetime.datetime(2026, 1, 15, 12), "de "),
    ],
)
def test_get_date_apostrophe(value, expected):
    """Élision avant un mois commençant par une voyelle (texte : a/o ; date : avril, août, octobre)"""
    assert get_date_apostrophe(value) == expected


@pytest.mark.parametrize(
    ("value", "last_day", "nb_days"),
    [
        (datetime.date(2024, 2, 10), datetime.date(2024, 2, 29), 29),
        (datetime.date(2023, 2, 10), datetime.date(2023, 2, 28), 28),
        (datetime.datetime(2026, 12, 1, 8), datetime.date(2026, 12, 31), 31),
        (datetime.date(2026, 4, 30), datetime.date(2026, 4, 30), 30),
    ],
)
def test_dernier_jour_et_nombre_de_jours_du_mois(value, last_day, nb_days):
    assert last_day_month(value) == last_day
    assert days_of_month(value) == nb_days


def test_date_string_series():
    """Date en AAAA_MM_JJ, année sur deux chiffres complétée, aujourd'hui par défaut"""
    today = datetime.date.today()

    assert date_string_series(datetime.date(2026, 1, 5)) == "2026_01_05"
    assert date_string_series(datetime.datetime(2026, 11, 25, 9)) == "2026_11_25"
    assert date_string_series(datetime.date(26, 1, 5)) == "2026_01_05"
    assert date_string_series() == f"{today.year}_{today.month:02d}_{today.day:02d}"


def test_time_string_series():
    """Secondes écoulées depuis le 01/01/2000, en texte"""
    before = int((datetime.datetime.now() - datetime.datetime(2000, 1, 1)).total_seconds())

    value = time_string_series()

    assert value.isdigit()
    assert before <= int(value) <= before + 2


def test_long_date_string():
    assert long_date_string(datetime.date(2026, 1, 17)) == "Janvier 2026"
    assert long_date_string(datetime.datetime(2025, 8, 1, 10)) == "Août 2025"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("2026-01-17", datetime.datetime(2026, 1, 17)),
        ("17/01/2026", datetime.datetime(2026, 1, 17)),
        ("17.01.2026", datetime.datetime(2026, 1, 17)),
        ("17-01-2026", datetime.datetime(2026, 1, 17)),
        ("20260117", datetime.datetime(2026, 1, 17)),
        ("17/01/26", datetime.datetime(2026, 1, 17)),
        ("  2026-01-17  ", datetime.datetime(2026, 1, 17)),
        (20260117, datetime.datetime(2026, 1, 17)),
    ],
)
def test_validate_date_formats_acceptes(value, expected):
    """Les six formats sont essayés dans l'ordre, les espaces sont ignorés"""
    assert validate_date(value) == expected
    assert len(DATE_FORMATS) == 6


@pytest.mark.parametrize("value", ["", "pas une date", "2026-13-01", "31/02/2026", None])
def test_validate_date_invalide(value):
    with pytest.raises(ValueError, match="validate_date"):
        validate_date(value)


# SQL ==============================================================================================


@pytest.mark.parametrize(
    ("value", "expected"),
    [(12, 12), ("12", 12), (" 7 ", 7), (3.7, 3), ("abc", 0), (None, 0), ("", 0), ([1], 0)],
)
def test_clean_id(value, expected):
    """Tout ce qui n'est pas convertible en entier vaut 0"""
    assert clean_id(value) == expected
