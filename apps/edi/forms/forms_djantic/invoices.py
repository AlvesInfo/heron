# pylint: disable=R0903,E0401
"""
FR : Module de validation par djantic des factures founisseurs
EN : Sage X3 import validation forms module for suppliers invoices

Commentaire:

created at: 2022-04-06
created by: Paulo ALVES

modified at: 2022-04-06
modified by: Paulo ALVES
"""
from decimal import Decimal
import uuid

from djantic import ModelSchema

from apps.core.validations.pydantic_validators_base import (
    TruncateStrFieldsBase,
    DecimalFieldBase,
    NullZeroDecimalFieldBase,
    GenericDateFieldsBase,
    DdMmYyyyyDateFieldsBase,
    IsoDateFieldsBase,
    IsoInverseDateFieldsBase,
    PointDateFieldsBase,
    TvaEyeConfor,
    TvaGenerique,
    TvaInterson,
    TvaWidex,
    TvaNewson,
)
from apps.edi.models import EdiImport, ColumnDefinition
from apps.edi.parameters.invoices_imports import get_columns


class BbrgBulkSchema(
    ModelSchema, TruncateStrFieldsBase, NullZeroDecimalFieldBase, DecimalFieldBase
):
    """Schema Djantic pour validation du modèle BbrgVerre"""

    uuid_identification: uuid.UUID
    supplier: str
    supplier_ident: str
    qty: Decimal = 1
    packaging_qty: Decimal = 1

    class Config:
        """Config"""

        model = EdiImport
        include = list(get_columns(ColumnDefinition, "BbrgBulk")) + ["uuid_identification"]


class EdiSchema(ModelSchema, TruncateStrFieldsBase, NullZeroDecimalFieldBase, DecimalFieldBase):
    """Schema Djantic pour validation du modèle Edi"""

    uuid_identification: uuid.UUID
    qty: Decimal = 1
    packaging_qty: Decimal = 1

    class Config:
        """Config"""

        model = EdiImport
        include = list(get_columns(ColumnDefinition, "Edi")) + ["uuid_identification"]


class EyeConfortSchema(
    ModelSchema,
    TruncateStrFieldsBase,
    NullZeroDecimalFieldBase,
    PointDateFieldsBase,
    TvaEyeConfor,
    DecimalFieldBase,
):
    """Schema Djantic pour validation du modèle Eye_confort"""

    uuid_identification: uuid.UUID
    supplier: str
    supplier_ident: str
    qty: Decimal = 1
    packaging_qty: Decimal = 1

    class Config:
        """Config"""

        model = EdiImport
        include = list(get_columns(ColumnDefinition, "EyeConfort")) + [
            "uuid_identification",
            "supplier",
            "supplier_ident",
        ]


class GeneriqueSchema(
    ModelSchema,
    TruncateStrFieldsBase,
    NullZeroDecimalFieldBase,
    GenericDateFieldsBase,
    TvaGenerique,
    DecimalFieldBase,
):
    """Schema Djantic pour validation du modèle Generique"""

    uuid_identification: uuid.UUID
    qty: Decimal = 1
    packaging_qty: Decimal = 1

    class Config:
        """Config"""

        model = EdiImport
        include = list(get_columns(ColumnDefinition, "Generique")) + ["uuid_identification"]


class HearingSchema(
    ModelSchema,
    TruncateStrFieldsBase,
    NullZeroDecimalFieldBase,
    IsoDateFieldsBase,
    TvaGenerique,
    DecimalFieldBase,
):
    """Schema Djantic pour validation du modèle Hearing"""

    uuid_identification: uuid.UUID = None
    supplier_ident: str
    qty: Decimal = 1
    packaging_qty: Decimal = 1

    class Config:
        """Config"""

        model = EdiImport
        include = list(get_columns(ColumnDefinition, "Hearing")) + [
            "uuid_identification",
            "supplier_ident",
        ]


class IntersonSchema(
    ModelSchema,
    TruncateStrFieldsBase,
    NullZeroDecimalFieldBase,
    DdMmYyyyyDateFieldsBase,
    TvaInterson,
    DecimalFieldBase,
):
    """Schema Djantic pour validation du modèle Interson"""

    uuid_identification: uuid.UUID
    qty: Decimal = 1
    packaging_qty: Decimal = 1
    devise: str = "EUR"

    class Config:
        """Config"""

        model = EdiImport
        include = list(get_columns(ColumnDefinition, "Interson")) + ["uuid_identification"]


class JohnsonSchema(
    ModelSchema,
    TruncateStrFieldsBase,
    NullZeroDecimalFieldBase,
    PointDateFieldsBase,
    DecimalFieldBase,
):
    """Schema Djantic pour validation du modèle Johnson"""

    uuid_identification: uuid.UUID
    supplier: str
    supplier_ident: str
    qty: Decimal = 1
    packaging_qty: Decimal = 1

    class Config:
        """Config"""

        model = EdiImport
        include = list(get_columns(ColumnDefinition, "Johnson")) + [
            "uuid_identification",
            "supplier",
            "supplier_ident",
        ]


class LmcSchema(
    ModelSchema,
    TruncateStrFieldsBase,
    NullZeroDecimalFieldBase,
    IsoDateFieldsBase,
    DecimalFieldBase,
):
    """Schema Djantic pour validation du modèle Lmc"""

    uuid_identification: uuid.UUID
    supplier_ident: str
    qty: Decimal = 1
    packaging_qty: Decimal = 1

    class Config:
        """Config"""

        model = EdiImport
        include = list(get_columns(ColumnDefinition, "Lmc")) + [
            "uuid_identification",
            "supplier_ident",
        ]


class NewsonSchema(
    ModelSchema,
    TruncateStrFieldsBase,
    NullZeroDecimalFieldBase,
    PointDateFieldsBase,
    TvaNewson,
    DecimalFieldBase,
):
    """Schema Djantic pour validation du modèle Newson"""

    uuid_identification: uuid.UUID
    supplier: str
    supplier_ident: str
    qty: Decimal = 1
    packaging_qty: Decimal = 1

    class Config:
        """Config"""

        model = EdiImport
        include = list(get_columns(ColumnDefinition, "Newson")) + [
            "uuid_identification",
            "supplier",
            "supplier_ident",
        ]


class PhonakSchema(
    ModelSchema,
    TruncateStrFieldsBase,
    NullZeroDecimalFieldBase,
    IsoDateFieldsBase,
    TvaGenerique,
    DecimalFieldBase,
):
    """Schema Djantic pour validation du modèle Phonak"""

    uuid_identification: uuid.UUID
    supplier_ident: str
    qty: Decimal = 1
    packaging_qty: Decimal = 1

    class Config:
        """Config"""

        model = EdiImport
        include = list(get_columns(ColumnDefinition, "Phonak")) + [
            "uuid_identification",
            "supplier_ident",
        ]


class ProditionSchema(
    ModelSchema,
    TruncateStrFieldsBase,
    NullZeroDecimalFieldBase,
    IsoDateFieldsBase,
    TvaGenerique,
    DecimalFieldBase,
):
    """Schema Djantic pour validation du modèle Prodition"""

    uuid_identification: uuid.UUID
    supplier_ident: str
    qty: Decimal = 1
    packaging_qty: Decimal = 1

    class Config:
        """Config"""

        model = EdiImport
        include = list(get_columns(ColumnDefinition, "Prodition")) + [
            "uuid_identification",
            "supplier_ident",
        ]


class SigniaSchema(
    ModelSchema,
    TruncateStrFieldsBase,
    NullZeroDecimalFieldBase,
    DdMmYyyyyDateFieldsBase,
    TvaWidex,
    DecimalFieldBase,
):
    """Schema Djantic pour validation du modèle Signia"""

    uuid_identification: uuid.UUID
    supplier: str
    supplier_ident: str
    qty: Decimal = 1
    packaging_qty: Decimal = 1

    class Config:
        """Config"""

        model = EdiImport
        include = list(get_columns(ColumnDefinition, "Signia")) + [
            "uuid_identification",
            "supplier",
            "supplier_ident",
        ]


class StarkeySchema(
    ModelSchema,
    TruncateStrFieldsBase,
    NullZeroDecimalFieldBase,
    IsoDateFieldsBase,
    TvaGenerique,
    DecimalFieldBase,
):
    """Schema Djantic pour validation du modèle Starkey"""

    uuid_identification: uuid.UUID
    supplier_ident: str
    qty: Decimal = 1
    packaging_qty: Decimal = 1

    class Config:
        """Config"""

        model = EdiImport
        include = list(get_columns(ColumnDefinition, "Starkey")) + [
            "uuid_identification",
            "supplier_ident",
        ]


class TechnidisSchema(
    ModelSchema,
    TruncateStrFieldsBase,
    NullZeroDecimalFieldBase,
    DdMmYyyyyDateFieldsBase,
    TvaWidex,
    DecimalFieldBase,
):
    """Schema Djantic pour validation du modèle Technidis"""

    uuid_identification: uuid.UUID
    qty: Decimal = 1
    packaging_qty: Decimal = 1

    class Config:
        """Config"""

        model = EdiImport
        include = list(get_columns(ColumnDefinition, "Technidis")) + ["uuid_identification"]


class UnitronSchema(
    ModelSchema,
    TruncateStrFieldsBase,
    NullZeroDecimalFieldBase,
    IsoDateFieldsBase,
    TvaGenerique,
    DecimalFieldBase,
):
    """Schema Djantic pour validation du modèle Unitron"""

    uuid_identification: uuid.UUID
    supplier_ident: str
    qty: Decimal = 1
    packaging_qty: Decimal = 1

    class Config:
        """Config"""

        model = EdiImport
        include = list(get_columns(ColumnDefinition, "Unitron")) + [
            "uuid_identification",
            "supplier_ident",
        ]


class WidexSchema(
    ModelSchema,
    TruncateStrFieldsBase,
    NullZeroDecimalFieldBase,
    IsoDateFieldsBase,
    TvaWidex,
    DecimalFieldBase,
):
    """Schema Djantic pour validation du modèle Widex"""

    uuid_identification: uuid.UUID
    supplier_ident: str
    qty: Decimal = 1
    packaging_qty: Decimal = 1

    class Config:
        """Config"""

        model = EdiImport
        include = list(get_columns(ColumnDefinition, "Widex")) + [
            "uuid_identification",
            "supplier_ident",
        ]


class WidexGaSchema(
    ModelSchema,
    TruncateStrFieldsBase,
    NullZeroDecimalFieldBase,
    IsoDateFieldsBase,
    TvaWidex,
    DecimalFieldBase,
):
    """Schema Djantic pour validation du modèle WidexGa"""

    uuid_identification: uuid.UUID
    supplier_ident: str
    qty: Decimal = 1
    packaging_qty: Decimal = 1

    class Config:
        """Config"""

        model = EdiImport
        include = list(get_columns(ColumnDefinition, "WidexGa")) + [
            "uuid_identification",
            "supplier_ident",
        ]
