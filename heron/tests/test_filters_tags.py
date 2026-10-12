# pylint: disable=E0401
"""
FR : Tests des filtres et balises de gabarit de heron (filters_tags)
EN : Tests for heron template filters and tags

Commentaire:

keep_br et trace_comment (échappement) sont testés dans apps/core/tests/test_templates_security.py.

created at: 2026-10-12
created by: Paulo ALVES
"""
from decimal import Decimal
from types import SimpleNamespace

import pytest
from django.template import Context, Template

from apps.core.bin.encoders import set_base_64_str
from heron.templatetags import filters_tags as ft


def render(source, **context):
    return Template("{% load filters_tags %}" + source).render(Context(context))


def test_filtres_de_texte():
    assert ft.keep_br("a<br>b & c") == "a<br>b &amp; c"
    assert ft.trace_comment(None) == ""
    assert ft.trace_comment("<div style='padding-left: 20px;'>x</div><br>") == '<div style="padding-left: 20px;">x</div><br>'
    assert ft.point("1,5") == "1.5"
    assert ft.get_is_str("x") is True
    assert ft.get_is_str(1) is False
    assert ft.get_dict_values({"a": 1, "b": 2}) == [1, 2]
    assert ft.get_dict_values(["a"]) is None
    assert ft.get_item({"a": 1}, "a") == 1
    assert ft.get_item({"a": 1}, "b") is None


@pytest.mark.parametrize(
    ("value", "expected"),
    [("05/01/26", "2026-01-05"), ("05/01/2026", "2026-01-05"), ("31/02/2026", ""), ("", ""), (None, "")],
)
def test_date_depuis_texte(value, expected):
    assert ft.date_from_str_4(value) == expected


@pytest.mark.parametrize(
    ("value", "num", "expected"),
    [
        (0, 2, "0"),
        (None, 2, "0"),
        ("1234.5", 2, "1234.50"),
        (1234, 0, "1234"),
        (1234, 2, "1234.00"),
        (Decimal("12.345"), 2, "12.34"),
    ],
)
def test_numbers(value, num, expected):
    assert ft.numbers(value, num) == expected


def test_numbersp():
    assert ft.numbersp(Decimal("0.155"), 1) == "15.5"
    assert ft.numbersp(Decimal("0.5"), 0) == "50"
    assert ft.numbersp(0, 1) == "0"


@pytest.mark.parametrize(
    ("value", "num", "expected"),
    [
        (Decimal("1234567.891"), 2, "1 234 567,89"),
        (Decimal("-1234.5"), 2, "-1 234,50"),
        (1234, 0, "1 234"),
        ("100", 2, "100,00"),
        (Decimal("0.00"), 2, "0"),
        (None, 2, "0"),
        (0, 2, "0"),
    ],
)
def test_numbers_format(value, num, expected):
    """Séparateur de milliers et décimales ; un entier ou un texte sans décimale ne plante plus"""
    assert ft.numbers_format(value, num) == expected


def test_int_formats_et_default_if_zero():
    assert ft.int_formats(1234567.9) == "1 234 567"
    assert ft.int_formats("12") == "12"
    assert ft.int_formats(0) == "0"
    assert ft.default_if_zero(0) == ""
    assert ft.default_if_zero("0") == ""
    assert ft.default_if_zero(5) == 5
    assert ft.default_if_zero(Decimal("0.00")) == Decimal("0.00")


def test_encodage_adresse_et_regroupement():
    assert ft.encode_b64_str("abc") == set_base_64_str("abc")
    assert ft.regroup_list_pipe("a", "b", "c") == "a||b||c"
    assert ft.get_address("Rue A||Bat B||75001||Paris") == "Rue A, Bat B - 75001 Paris"
    assert ft.get_address("Rue A||||75001||Paris") == "Rue A - 75001 Paris"
    assert ft.get_address("Rue A||||") == "Rue A"
    assert ft.get_address("||75001||Paris") == " - 75001 Paris"
    assert ft.get_address("||||") == ""
    assert ft.percentage(None) == ""
    assert ft.percentage(0.1234) == "12.3%"
    assert ft.regroup_sum([SimpleNamespace(net_amount=Decimal("10")), {"net_amount": Decimal("5")}, {}], "net_amount") == Decimal("15")
    assert ft.regroup_sum([], "net_amount") == 0


@pytest.mark.parametrize(
    ("value", "expected"),
    [("12345678901234", "123 456 789 01234"), ("123-456 789_012", "123 456 789 012"), ("", ""), (None, "Non e")],
)
def test_siret(value, expected):
    assert ft.siret_number(value) == expected


def test_filtres_enregistres_dans_les_gabarits():
    """Les filtres et balises sont bien chargés par {% load filters_tags %}"""
    assert render("{{ v|numbers_format:2 }}", v=Decimal("1234.5")) == "1 234,50"
    assert render("{{ v|numbers:1 }}", v=Decimal("2.25")) == "2.2"
    assert render("{{ v|percentage }}", v=0.5) == "50.0%"
    assert render("{{ v|siret_number }}", v="12345678901234") == "123 456 789 01234"
    assert render("{% regroup_list_pipe 'a' 'b' %}") == "a||b"
    assert render("{% get_address 'Rue||75001||Paris' %}") == "Rue - 75001 Paris"
    assert render("{{ d|get_item:'k' }}", d={"k": "v"}) == "v"
    assert sorted(ft.register.filters) == [
        "date_from_str_4", "default_if_zero", "encode_b64_str", "get_dict_values", "get_item", "int_formats",
        "is_str", "keep_br", "numbers", "numbers_format", "numbersp", "percentage", "point", "regroup_sum",
        "siret_number", "trace_comment",
    ]
    assert sorted(ft.register.tags) == ["get_address", "regroup_list_pipe"]
