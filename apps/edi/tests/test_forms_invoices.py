"""Tests de la construction paresseuse des schémas djantic des flux fournisseurs (directive D1)"""

import datetime
import importlib.util
import uuid
from decimal import Decimal
from pathlib import Path

import pytest
from django.core.exceptions import ImproperlyConfigured

from apps.edi.forms.forms_djantic import forms_invoices
from apps.edi.forms.forms_djantic.forms_invoices import (
    DEFAULT_DATE,
    SCHEMA_DEFINITIONS,
    build_schema,
    default_date,
    get_schema,
)
from conftest import captured_queries

EDI_COLUMNS = [
    ("invoice_number", "1"),
    ("invoice_date", "2"),
    ("qty", "3"),
    ("acuitis_order_date", "4"),
    ("delivery_date", "5"),
    ("net_amount", "montant"),
]


def load_module_copy(module):
    """Exécute le source d'un module sous un nouveau nom : on observe son import sans recharger

    le module réel (un reload recréerait get_schema et son cache pour les autres tests).
    """
    spec = importlib.util.spec_from_file_location(f"{module.__name__}_copy", Path(module.__file__))
    copy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(copy)
    return copy


@pytest.mark.django_db
def test_module_import_does_not_query_database():
    """L'import du module ne lit plus edi.ColumnDefinition"""
    with captured_queries() as queries:
        copy = load_module_copy(forms_invoices)

    assert queries.captured_queries == []
    assert set(copy.SCHEMA_DEFINITIONS) == set(SCHEMA_DEFINITIONS)


@pytest.mark.django_db
def test_pool_import_does_not_query_database():
    """Le pool d'import, seul consommateur des schémas, s'importe sans requête"""
    from apps.edi.imports import imports_suppliers_invoices_pool  # pylint: disable=C0415

    with captured_queries() as queries:
        copy = load_module_copy(imports_suppliers_invoices_pool)

    assert queries.captured_queries == []
    assert copy.get_schema is forms_invoices.get_schema


@pytest.mark.parametrize("value", ["", None, "None", 0])
def test_default_date_replaces_empty_values(value):
    assert default_date(value) == DEFAULT_DATE


def test_default_date_keeps_values():
    assert default_date("2024-05-01") == "2024-05-01"


def test_definitions_cover_all_supplier_flows():
    """Chaque définition déclare les colonnes ajoutées par le loader et un flux"""
    assert len(SCHEMA_DEFINITIONS) == 22

    for name, definition in SCHEMA_DEFINITIONS.items():
        assert name.endswith("Schema")
        assert definition.flow_name
        assert "uuid_identification" in definition.fields
        assert set(definition.extra_columns) >= {
            "uuid_identification",
            "flow_name",
            "created_at",
            "modified_at",
        }
        assert set(definition.default_date_fields) <= set(definition.fields)
        assert set(definition.defaults) <= set(definition.fields)


def test_build_schema_without_column_definitions_raises(make_column_definitions):
    make_column_definitions("Edi", [])

    with pytest.raises(ImproperlyConfigured, match="flux 'Edi'.*EdiSchema"):
        build_schema("EdiSchema", SCHEMA_DEFINITIONS["EdiSchema"])


def test_build_schema_includes_file_columns_and_loader_columns(make_column_definitions):
    make_column_definitions("Edi", EDI_COLUMNS)

    schema = build_schema("EdiSchema", SCHEMA_DEFINITIONS["EdiSchema"])

    assert schema.__name__ == "EdiSchema"
    assert schema.__module__ == forms_invoices.__name__
    assert schema.__config__.include == [column for column, _ in EDI_COLUMNS] + [
        "uuid_identification",
        "flow_name",
        "created_at",
        "modified_at",
    ]
    assert set(schema.__fields__) == set(schema.__config__.include)
    assert schema.__fields__["qty"].default == 1
    assert schema.__fields__["uuid_identification"].required


def test_built_schema_validates_like_before(make_column_definitions):
    """Dates vides remplacées par 1900-01-01, décimaux vides à zéro, qty par défaut si absente"""
    make_column_definitions("Edi", EDI_COLUMNS)
    schema = build_schema("EdiSchema", SCHEMA_DEFINITIONS["EdiSchema"])
    identification = uuid.uuid4()

    validated = schema(
        uuid_identification=identification,
        flow_name="Edi",
        created_at="2024-01-05",
        modified_at="2024-01-05",
        invoice_number="F001",
        invoice_date="2024-01-05",
        acuitis_order_date="None",
        delivery_date="",
        net_amount="",
    )

    assert validated.uuid_identification == identification
    assert validated.acuitis_order_date == datetime.datetime(1900, 1, 1)
    assert validated.delivery_date == datetime.datetime(1900, 1, 1)
    assert validated.net_amount == Decimal(0)
    assert validated.qty == Decimal(1)
    assert schema(**{**validated.dict(), "qty": ""}).qty == Decimal(0)


def test_build_schema_applies_mixins_and_defaults(make_column_definitions):
    make_column_definitions("Zburefac", [("invoice_number", "1"), ("vat_rate", "2")])

    schema = build_schema("ZBuRefacSageSchema", SCHEMA_DEFINITIONS["ZBuRefacSageSchema"])

    assert schema.__fields__["flow_name"].default == "SageYoozRefac"
    assert schema.__fields__["supplier"].default == "SAGE_YOOZ_REFAC"
    assert schema.__fields__["supplier_ident"].default == "Zburefac"
    assert "ValidateFieldsBase" in [base.__name__ for base in schema.__mro__]


def test_build_schema_can_be_called_twice(make_column_definitions):
    """Les validateurs partagés sont réutilisables : pas d'erreur 'duplicate validator'"""
    make_column_definitions("Johnson", [("invoice_number", "1"), ("delivery_date", "2")])
    definition = SCHEMA_DEFINITIONS["JohnsonSchema"]

    first = build_schema("JohnsonSchema", definition)
    second = build_schema("JohnsonSchema", definition)

    assert first is not second
    assert first.__config__.include == second.__config__.include
    assert (
        first(
            uuid_identification=uuid.uuid4(),
            flow_name="Johnson",
            supplier="JOHNSON",
            supplier_ident="Johnson",
            created_at="2024-01-05",
            modified_at="2024-01-05",
            invoice_number="F001",
            delivery_date=None,
        ).delivery_date
        == DEFAULT_DATE
    )


@pytest.mark.usefixtures("schema_cache_cleared")
def test_get_schema_is_cached(make_column_definitions):
    make_column_definitions("Widex", [("invoice_number", "1")])

    with captured_queries() as queries:
        first = get_schema("WidexSchema")
        second = get_schema("WidexSchema")

    assert first is second
    assert len(queries.captured_queries) == 1


@pytest.mark.usefixtures("schema_cache_cleared")
def test_get_schema_unknown_name():
    with pytest.raises(KeyError, match="Schéma 'InconnuSchema' inconnu.*WidexSchema"):
        get_schema("InconnuSchema")


@pytest.mark.django_db
@pytest.mark.usefixtures("column_definitions_data", "schema_cache_cleared")
def test_get_schema_with_production_snapshot():
    """Toutes les définitions se construisent sur l'instantané de production"""
    schemas = {name: get_schema(name) for name in SCHEMA_DEFINITIONS}

    assert all(len(schema.__config__.include) > 4 for schema in schemas.values())
    assert {schema.__config__.model for schema in schemas.values()} == {forms_invoices.EdiImport}
