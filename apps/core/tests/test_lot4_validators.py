# pylint: disable=E0401,W0621
"""FR : Tests des validateurs de base pydantic (apps/core/validations/pydantic_validators_base.py),


     du séparateur décimal de forms_base et des champs de sérialiseur (functions_serializers.py)
EN : Tests for base pydantic validators, forms_base decimal separator and serializer fields

created at: 2026-10-11
created by: Paulo ALVES
"""

import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError, constr
from rest_framework import serializers

from apps.core.functions.functions_serializers import MaxLenghtCharField, NullBooleanField
from apps.core.validations.forms_base import NullZeroDecimalField
from apps.core.validations.pydantic_validators_base import (
    DecimalFieldBase,
    ExcelDateFieldsBase,
    NullZeroDecimalFieldBase,
    SageDateFieldsBase,
    SageDefaultDateFieldsBase,
    SageNullBooleanFieldsBase,
    SageNullFalseBooleanFieldsBase,
    SageTruncateStrFieldsBase,
    TruncateStrFieldsBase,
    TvaEyeConfor,
    TvaGenerique,
    TvaInterson,
    TvaNewson,
    TvaWidex,
    ValidateFieldsBase,
)

# VALIDATEUR GÉNÉRIQUE =============================================================================


class Generic(ValidateFieldsBase):
    """Texte tronqué, décimal à zéro par défaut, date multi formats"""

    name: constr(max_length=5) | None  # type: ignore[valid-type]
    amount: Decimal | None
    day: datetime.date | None


def test_validate_fields_base_texte_et_decimal():
    validated = Generic(name="  abc~~def ghijkl", amount="1 234,5", day=None)

    assert validated.name == "abc"
    assert validated.amount == Decimal("1234.5")
    assert Generic(name="", amount="", day=None).name is None
    assert Generic(name=None, amount=None, day=None).amount is None
    assert Generic(name="x", amount="12.5%", day=None).amount == Decimal("12.5")


@pytest.mark.parametrize(
    "value",
    ["2026-01-15", "15/01/2026", "15.01.2026", "2026.01.15", "15-01-2026", "20260115", "15/01/26"],
)
def test_validate_fields_base_formats_de_date(value):
    assert Generic(name="x", amount="0", day=f" {value} ").day == datetime.date(2026, 1, 15)


def test_validate_fields_base_date_non_reconnue():
    with pytest.raises(ValidationError):
        Generic(name="x", amount="0", day="janvier 2026")

    assert Generic(name="x", amount="0", day=datetime.date(2026, 2, 1)).day == datetime.date(
        2026, 2, 1
    )


# TEXTE ============================================================================================


class Texts(TruncateStrFieldsBase):
    name: constr(max_length=4) | None  # type: ignore[valid-type]
    number: int


class SageTexts(SageTruncateStrFieldsBase):
    name: constr(max_length=4) | None  # type: ignore[valid-type]
    number: int = 0


@pytest.mark.parametrize("model", [Texts, SageTexts])
def test_troncature_des_textes(model):
    kwargs = {"number": 1} if model is Texts else {}

    assert model(name=" abcdef~~ignoré ", **kwargs).name == "abcd"
    assert model(name="", **kwargs).name is None
    assert model(name=None, **kwargs).name is None


def test_troncature_laisse_les_autres_champs():
    assert Texts(name="a", number="12").number == 12
    assert SageTexts(name="a", number="7").number == 7


# BOOLÉENS =========================================================================================


class NullBooleans(SageNullBooleanFieldsBase):
    flag: bool | None
    name: str = "x"


class FalseBooleans(SageNullFalseBooleanFieldsBase):
    flag: bool
    name: str


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("2", True),
        ("OUI", True),
        ("1", False),
        ("", False),
        ("faux", False),
        ("peut-être", None),
        (None, None),
    ],
)
def test_booleens_sage_nullables(value, expected):
    validated = NullBooleans(flag=value, name="y")

    assert validated.flag is expected
    assert validated.name == "y"


@pytest.mark.parametrize(
    ("value", "expected"),
    [("2.0", True), ("vrai", True), ("1", False), ("", False), ("autre", False), (None, False)],
)
def test_booleens_sage_faux_par_defaut(value, expected):
    validated = FalseBooleans(flag=value, name="x")

    assert validated.flag is expected
    assert validated.name == "x"


# DÉCIMAUX =========================================================================================


class Decimals(DecimalFieldBase):
    amount: Decimal | None
    name: str


class ZeroDecimals(NullZeroDecimalFieldBase):
    amount: Decimal
    name: str


def test_decimaux():
    assert Decimals(amount="1.234,50", name="x").amount == Decimal("1234.50")
    assert Decimals(amount=None, name="x").amount is None
    assert Decimals(amount="7", name="y").name == "y"
    assert ZeroDecimals(amount="", name="x").amount == Decimal(0)
    assert ZeroDecimals(amount="2,5", name="x").amount == Decimal("2.5")
    assert ZeroDecimals(amount="1", name="z").name == "z"


# DATES ============================================================================================


class SageDates(SageDateFieldsBase):
    day: datetime.date | None
    name: str


class ExcelDates(ExcelDateFieldsBase):
    day: datetime.date | None
    name: str


class DefaultDates(SageDefaultDateFieldsBase):
    day: datetime.date
    name: str


def test_dates_sage():
    assert SageDates(day=" 150126 ", name="x").day == datetime.date(2026, 1, 15)
    assert SageDates(day="", name="x").day is None
    assert SageDates(day=datetime.date(2026, 1, 1), name="x").day == datetime.date(2026, 1, 1)
    assert SageDates(day=None, name="y").name == "y"


def test_dates_excel():
    assert ExcelDates(day="15/01/2026", name="x").day == datetime.date(2026, 1, 15)
    assert ExcelDates(day="  ", name="x").day is None
    assert ExcelDates(day=None, name="y").name == "y"

    with pytest.raises(ValidationError):
        ExcelDates(day="2026-01-15", name="x")


def test_dates_sage_par_defaut():
    assert DefaultDates(day="150126", name="x").day == datetime.date(2026, 1, 15)
    assert DefaultDates(day="", name="x").day == datetime.date(1900, 1, 1)
    assert DefaultDates(day="None", name="x").day == datetime.date(1900, 1, 1)
    assert DefaultDates(day=datetime.date(2026, 3, 1), name="y").day == datetime.date(2026, 3, 1)


# TVA ==============================================================================================


def _vat_model(base):
    class Vat(base):
        vat_rate: Decimal

    return Vat


@pytest.mark.parametrize(
    ("value", "expected"),
    [("20%", Decimal("0.20")), ("5%5", Decimal("0.055")), ("0.2", Decimal("0.2"))],
)
def test_tva_eye_confort(value, expected):
    assert _vat_model(TvaEyeConfor)(vat_rate=value).vat_rate == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("2000", Decimal("0.2")),
        ("0550.0", Decimal("0.055")),
        ("0", Decimal(0)),
        ("", Decimal(0)),
        ("0.2", Decimal("0.2")),
    ],
)
def test_tva_generique(value, expected):
    assert _vat_model(TvaGenerique)(vat_rate=value).vat_rate == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1", Decimal("0.2")),
        (2, Decimal("0.055")),
        ("", Decimal(0)),
        (None, Decimal(0)),
        ("0.1", Decimal("0.1")),
    ],
)
def test_tva_interson(value, expected):
    assert _vat_model(TvaInterson)(vat_rate=value).vat_rate == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("20,00", Decimal("0.2")),
        ("06", Decimal("0.055")),
        ("5.50", Decimal("0.055")),
        ("020.0", Decimal("0.2")),
        ("00.0", Decimal(0)),
        ("", Decimal(0)),
        ("0.1", Decimal("0.1")),
        (0, Decimal(0)),
    ],
)
def test_tva_widex(value, expected):
    assert _vat_model(TvaWidex)(vat_rate=value).vat_rate == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("C0", Decimal(0)),
        ("E7", Decimal(0)),
        ("C3", Decimal("0.055")),
        ("C4", Decimal("0.2")),
        ("0.1", Decimal("0.1")),
    ],
)
def test_tva_newson(value, expected):
    assert _vat_model(TvaNewson)(vat_rate=value).vat_rate == expected


# SÉPARATEUR DÉCIMAL DU FORMULAIRE =================================================================


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1,234.5", Decimal("1234.5")),
        ("1.234,5", Decimal("1234.5")),
        ("1 234", Decimal(1234)),
        ("2,5", Decimal("2.5")),
        (None, Decimal(0)),
    ],
)
def test_null_zero_decimal_field_separateurs(value, expected):
    """Le premier séparateur rencontré est celui des milliers"""
    assert (
        NullZeroDecimalField(localize=False).clean(
            value.replace(" ", "") if isinstance(value, str) else value
        )
        == expected
    )


# CHAMPS DE SÉRIALISEUR ============================================================================


class Row(serializers.Serializer):
    flag = NullBooleanField(allow_null=True)
    name = MaxLenghtCharField(max_length=4, allow_blank=True)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1", True),
        ("2.0", True),
        ("0", False),
        ("-1", False),
        ("oui", True),
        ("X", True),
        ("non", False),
        ("-", False),
        ("", None),
        ("nul", None),
        ("true", True),
        ("false", False),
    ],
)
def test_null_boolean_field(value, expected):
    row = Row(data={"flag": value, "name": "x"})

    assert row.is_valid(), row.errors
    assert row.validated_data["flag"] is expected


@pytest.mark.parametrize("value", ["peut-être", ["liste"]])
def test_null_boolean_field_invalide(value):
    row = Row(data={"flag": value, "name": "x"})

    assert row.is_valid() is False
    assert "flag" in row.errors


def test_null_boolean_field_nul_sans_allow_null():
    class Strict(serializers.Serializer):
        flag = NullBooleanField()

    strict = Strict(data={"flag": "nulle"})

    assert strict.is_valid() is False


@pytest.mark.parametrize(
    ("value", "expected"), [("  abcdef ", "abcd"), (12345, "1234"), (1.5, "1.5"), ("", "")]
)
def test_max_length_char_field(value, expected):
    row = Row(data={"flag": "1", "name": value})

    assert row.is_valid(), row.errors
    assert row.validated_data["name"] == expected


@pytest.mark.parametrize("value", [True, ["a"], {"a": 1}])
def test_max_length_char_field_invalide(value):
    row = Row(data={"flag": "1", "name": value})

    assert row.is_valid() is False
    assert "name" in row.errors
