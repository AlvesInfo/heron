# pylint: disable=E0401,W0621
"""FR : Tests des utilitaires génériques (apps/core/functions/functions_utilitaires.py)


EN : Tests for generic utilities

created at: 2026-10-11
created by: Paulo ALVES
"""

import datetime
import logging
from decimal import Decimal
from pathlib import Path

import pytest
from django.test import RequestFactory

from apps.core.functions import functions_utilitaires
from apps.core.functions.functions_utilitaires import (
    EncodingError,
    Timer,
    alpha,
    delete_file,
    encoding_detect,
    format_siret,
    get_client_ip,
    get_decimal,
    get_module_object,
    get_zero_decimal,
    iter_slice,
    num_string_series,
    overlaps,
    pages,
    slicing_parser,
)


@pytest.mark.parametrize(
    ("first", "second", "expected"),
    [
        ([0, 3], [3, 4], True),
        ([3, 4], [0, 3], True),
        ([0, 3], [4, 6], False),
        ([0, 3], [-4, -6], False),
        (
            [datetime.date(2022, 1, 1), datetime.date(2022, 1, 3)],
            [datetime.date(2022, 1, 2), datetime.date(2022, 1, 2)],
            True,
        ),
        (
            [datetime.date(2022, 1, 1), datetime.date(2022, 1, 3)],
            [datetime.date(2022, 1, 6), datetime.date(2022, 1, 8)],
            False,
        ),
    ],
)
def test_overlaps(first, second, expected):
    """Chevauchement d'intervalles de nombres ou de dates, bornes incluses"""
    assert overlaps(first, second) is expected


@pytest.mark.parametrize(
    ("num", "nb_car", "expected"),
    [(18, 10, "0000000018"), (0, 3, "000"), (-7, 4, "0007"), ("42", 2, "42"), (123456, 3, "456")],
)
def test_num_string_series(num, nb_car, expected):
    """Numéro complété de zéros à gauche sur le nombre de caractères voulu"""
    assert num_string_series(num, nb_car) == expected


def test_iter_slice():
    """Découpage d'un itérable par tranches, dernière tranche incomplète, format au choix"""
    assert list(iter_slice([1, 2, 3, 4, 5, 6, 7, 8, 9], 4)) == [(1, 2, 3, 4), (5, 6, 7, 8), (9,)]
    assert list(iter_slice("abcd", 2, form=list)) == [["a", "b"], ["c", "d"]]
    assert list(iter_slice([], 3)) == []


def test_timer(caplog):
    """Le chronomètre journalise la durée à la sortie du bloc et s'affiche en cours de route"""
    with caplog.at_level(logging.INFO, logger="django"), Timer() as timer:
        assert str(timer).startswith("intermédiaire : ")

    assert caplog.records[-1].getMessage().endswith("s")


@pytest.mark.parametrize(
    ("value", "expected"),
    [(" 12.0 ", "12"), ("a\tb\r\nc", "abc"), (12.0, "12"), ("1.50", "1.50"), (None, "None")],
)
def test_alpha(value, expected):
    """Suppression des tabulations, retours à la ligne, espaces et du .0 final"""
    assert alpha(value) == expected


def test_pages():
    assert pages(None) is None
    assert pages([1, 2]) == [1, 2]


def test_delete_file(tmp_path):
    """Le fichier est supprimé s'il existe, sans erreur sinon"""
    path = tmp_path / "a_supprimer.txt"
    path.write_text("x", encoding="utf8")

    delete_file(path)
    delete_file(path)

    assert not path.exists()


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        ("ligne simple sans accent\n" * 20, "ascii"),
        ("énergie électrique été à côté\n" * 20, "utf-8"),
    ],
)
def test_encoding_detect(tmp_path, content, expected):
    path = tmp_path / "fichier.csv"
    path.write_text(content, encoding="utf8")

    assert encoding_detect(path) == expected


def test_encoding_detect_latin_1(tmp_path):
    path = tmp_path / "fichier.csv"
    path.write_bytes("énergie électrique été à côté\n".encode("latin-1") * 20)

    assert encoding_detect(path).lower() in {
        "iso-8859-1",
        "windows-1252",
        "iso-8859-9",
        "windows-1254",
    }


def test_encoding_detect_fichier_absent(tmp_path):
    with pytest.raises(EncodingError, match="encoding_detect : 'absent.csv'"):
        encoding_detect(tmp_path / "absent.csv")


def test_slicing_parser():
    """Découpe d'une ligne à largeurs fixes"""
    parser = slicing_parser([2, 5, 4])

    assert parser("ABCDEFGHIJKLMN") == ("AB", "CDEFG", "HIJK")
    assert slicing_parser([3])("ABCDE") == "ABC"


def test_get_client_ip():
    """Adresse derrière un proxy (X-Forwarded-For) sinon adresse distante"""
    factory = RequestFactory()

    assert (
        get_client_ip(
            factory.get("/", HTTP_X_FORWARDED_FOR="10.0.0.1, 10.0.0.2", REMOTE_ADDR="127.0.0.1")
        )
        == "10.0.0.1"
    )
    assert get_client_ip(factory.get("/", REMOTE_ADDR="192.168.1.10")) == "192.168.1.10"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1 234,56", "1234.56"),
        ("1,234.56", "1234.56"),
        ("1.234,56", "1234.56"),
        ("-12,5", "-12.5"),
        ("+3", "+3"),
        ("abc", "abc"),
        (Decimal("2.5"), "2.5"),
        ("", ""),
    ],
)
def test_get_decimal(value, expected):
    """Normalisation des décimaux français ou anglais en notation à point"""
    assert get_decimal(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("20 %", "20"),
        ("1.234,5", "1234.5"),
        ("1,234.5", "1234.5"),
        ("", "0"),
        ("-1", "-1"),
        ("12,5", "12.5"),
    ],
)
def test_get_zero_decimal(value, expected):
    """Comme get_decimal, sans le signe, le % retiré et zéro par défaut"""
    assert get_zero_decimal(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, ""),
        ("", ""),
        ("123456789", "123 456 789"),
        ("123 456 789 00012", "123 456 789 00012"),
        ("12345678900012", "123 456 789 00012"),
        ("12AB", "12AB"),
        (123456789, "123 456 789"),
    ],
)
def test_format_siret(value, expected):
    assert format_siret(value) == expected


def test_get_module_object():
    """Résolution d'un objet par son chemin pointé"""
    assert get_module_object("apps.core.functions.functions_utilitaires.alpha") is alpha
    assert get_module_object("pathlib.Path") is Path

    with pytest.raises(AttributeError):
        get_module_object("apps.core.functions.functions_utilitaires.inexistante")


def test_table_de_translitteration_sans_doublon():
    """Chaque caractère accentué n'est rattaché qu'à une lettre de base"""
    letters = [char for chars in functions_utilitaires.N_DIC.values() for char in chars]

    assert len(letters) == len(set(letters))
