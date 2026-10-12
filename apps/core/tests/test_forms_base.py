"""
Tests des champs de formulaire de validation de apps.core (forms_base)
"""
import datetime
from decimal import Decimal

import pytest
from django import forms

from apps.core.validations.forms_base import (
    DefaultDateField,
    DefaultDateTodayField,
    FrenchBooleanField,
    FrenchNullBooleanField,
    NullZeroDecimalField,
    SageNullBooleanField,
    TildeTextField,
    TruncatedTextField,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, Decimal("0")),
        ("", Decimal("0")),
        ("12,5", Decimal("12.5")),
        ("1.234,56", Decimal("1234.56")),
        ("1,234.56", Decimal("1234.56")),
        (Decimal("3.5"), Decimal("3.5")),
        (7, Decimal("7")),
    ],
)
def test_null_zero_decimal_field(value, expected):
    """Valeur absente -> 0, séparateurs français et anglais normalisés, nombres typés acceptés"""
    assert NullZeroDecimalField().clean(value) == expected


def test_null_zero_decimal_field_dans_un_formulaire_sans_la_cle():
    """Le champ absent du POST ne fait plus planter le formulaire (TypeError sur int)"""

    class Form(forms.Form):
        montant = NullZeroDecimalField()

    form = Form({})

    assert form.is_valid(), form.errors
    assert form.cleaned_data["montant"] == Decimal("0")


@pytest.mark.parametrize(("value", "expected"), [("abcdef", "abc"), (None, ""), ("ab", "ab")])
def test_truncated_text_field(value, expected):
    assert TruncatedTextField(max_length=3, required=False).clean(value) == expected


@pytest.mark.parametrize(("value", "expected"), [("Paris~~Paris", "Paris"), ("Lyon", "Lyon"), (None, "")])
def test_tilde_text_field(value, expected):
    assert TildeTextField(required=False).clean(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [("oui", True), ("1", True), ("vrai", True), ("non", False), ("", False), ("peut-être", False)],
)
def test_french_boolean_field(value, expected):
    assert FrenchBooleanField(required=False).clean(value) is expected


@pytest.mark.parametrize(("value", "expected"), [("oui", True), ("faux", False), ("", None)])
def test_french_null_boolean_field(value, expected):
    field = FrenchNullBooleanField(required=False)

    if expected is None:
        assert field.clean(value) is False  # BooleanField : None devient False
    else:
        assert field.clean(value) is expected


@pytest.mark.parametrize(("value", "expected"), [("2", True), ("2.0", True), ("1", False), ("", None), ("x", None)])
def test_sage_null_boolean_field(value, expected):
    assert SageNullBooleanField().clean(value) is expected


def test_default_date_fields():
    assert DefaultDateTodayField().clean("") == datetime.date.today()
    assert DefaultDateField().clean("") == datetime.date(2000, 1, 1)
