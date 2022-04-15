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
    ValidateFieldsBase,
    TvaEyeConfor,
    TvaGenerique,
    TvaInterson,
    TvaWidex,
    TvaNewson,
)
from apps.edi.models import EdiImport, ColumnDefinition
from apps.edi.parameters.invoices_imports import get_columns


class BbrgBulkSchema(
    ModelSchema,
    ValidateFieldsBase,
    TvaWidex,
):
    """Schema Djantic pour validation du modèle BbrgVerre"""

    uuid_identification: uuid.UUID
    supplier: str
    supplier_ident: str

    class Config:
        """Config"""

        model = EdiImport
        include = list(get_columns(ColumnDefinition, "BbrgBulk")) + [
            "uuid_identification",
            "flow_name",
            "supplier",
            "supplier_ident",
        ]


class EdiSchema(
    ModelSchema,
    ValidateFieldsBase,
):
    """Schema Djantic pour validation du modèle Edi"""

    uuid_identification: uuid.UUID
    qty: Decimal = 1

    class Config:
        """Config"""

        model = EdiImport
        include = list(get_columns(ColumnDefinition, "Edi")) + [
            "uuid_identification",
            "flow_name",
            "supplier",
            "supplier_ident",
        ]


class EyeConfortSchema(
    ModelSchema,
    ValidateFieldsBase,
    TvaEyeConfor,
):
    """Schema Djantic pour validation du modèle Eye_confort"""

    uuid_identification: uuid.UUID
    supplier: str
    supplier_ident: str

    class Config:
        """Config"""

        model = EdiImport
        include = list(get_columns(ColumnDefinition, "EyeConfort")) + [
            "uuid_identification",
            "flow_name",
            "supplier",
            "supplier_ident",
        ]


class GeneriqueSchema(
    ModelSchema,
    ValidateFieldsBase,
    TvaGenerique,
):
    """Schema Djantic pour validation du modèle Generique"""

    uuid_identification: uuid.UUID

    class Config:
        """Config"""

        model = EdiImport
        include = list(get_columns(ColumnDefinition, "Generique")) + [
            "uuid_identification",
            "flow_name",
        ]


class HearingSchema(
    ModelSchema,
    ValidateFieldsBase,
    TvaGenerique,
):
    """Schema Djantic pour validation du modèle Hearing"""

    uuid_identification: uuid.UUID
    supplier: str
    supplier_ident: str

    class Config:
        """Config"""

        model = EdiImport
        include = list(get_columns(ColumnDefinition, "Hearing")) + [
            "uuid_identification",
            "flow_name",
            "supplier",
            "supplier_ident",
        ]


class IntersonSchema(
    ModelSchema,
    ValidateFieldsBase,
    TvaInterson,
):
    """Schema Djantic pour validation du modèle Interson"""

    uuid_identification: uuid.UUID
    supplier: str
    supplier_ident: str

    class Config:
        """Config"""

        model = EdiImport
        include = list(get_columns(ColumnDefinition, "Interson")) + [
            "uuid_identification",
            "flow_name",
            "supplier",
            "supplier_ident",
        ]


class JohnsonSchema(
    ModelSchema,
    ValidateFieldsBase,
):
    """Schema Djantic pour validation du modèle Johnson"""

    uuid_identification: uuid.UUID
    supplier: str
    supplier_ident: str

    class Config:
        """Config"""

        model = EdiImport
        include = list(get_columns(ColumnDefinition, "Johnson")) + [
            "uuid_identification",
            "flow_name",
            "supplier",
            "supplier_ident",
        ]


class LmcSchema(
    ModelSchema,
    ValidateFieldsBase,
):
    """Schema Djantic pour validation du modèle Lmc"""

    uuid_identification: uuid.UUID
    supplier: str
    supplier_ident: str

    class Config:
        """Config"""

        model = EdiImport
        include = list(get_columns(ColumnDefinition, "Lmc")) + [
            "uuid_identification",
            "flow_name",
            "supplier",
            "supplier_ident",
        ]


class NewsonSchema(
    ModelSchema,
    ValidateFieldsBase,
    TvaNewson,
):
    """Schema Djantic pour validation du modèle Newson"""

    uuid_identification: uuid.UUID
    supplier: str
    supplier_ident: str

    class Config:
        """Config"""

        model = EdiImport
        include = list(get_columns(ColumnDefinition, "Newson")) + [
            "uuid_identification",
            "flow_name",
            "supplier",
            "supplier_ident",
        ]


class PhonakSchema(
    ModelSchema,
    ValidateFieldsBase,
    TvaGenerique,
):
    """Schema Djantic pour validation du modèle Phonak"""

    uuid_identification: uuid.UUID
    supplier: str
    supplier_ident: str

    class Config:
        """Config"""

        model = EdiImport
        include = list(get_columns(ColumnDefinition, "Phonak")) + [
            "uuid_identification",
            "flow_name",
            "supplier",
            "supplier_ident",
        ]


class ProditionSchema(
    ModelSchema,
    ValidateFieldsBase,
    TvaGenerique,
):
    """Schema Djantic pour validation du modèle Prodition"""

    uuid_identification: uuid.UUID
    supplier: str
    supplier_ident: str

    class Config:
        """Config"""

        model = EdiImport
        include = list(get_columns(ColumnDefinition, "Prodition")) + [
            "uuid_identification",
            "flow_name",
            "supplier",
            "supplier_ident",
        ]


class SigniaSchema(
    ModelSchema,
    ValidateFieldsBase,
    TvaWidex,
):
    """Schema Djantic pour validation du modèle Signia"""

    uuid_identification: uuid.UUID
    supplier: str
    supplier_ident: str

    class Config:
        """Config"""

        model = EdiImport
        include = list(get_columns(ColumnDefinition, "Signia")) + [
            "uuid_identification",
            "flow_name",
            "supplier",
            "supplier_ident",
        ]


class StarkeySchema(
    ModelSchema,
    ValidateFieldsBase,
    TvaGenerique,
):
    """Schema Djantic pour validation du modèle Starkey"""

    uuid_identification: uuid.UUID
    supplier: str
    supplier_ident: str

    class Config:
        """Config"""

        model = EdiImport
        include = list(get_columns(ColumnDefinition, "Starkey")) + [
            "uuid_identification",
            "flow_name",
            "supplier",
            "supplier_ident",
        ]


class TechnidisSchema(
    ModelSchema,
    ValidateFieldsBase,
    TvaWidex,
):
    """Schema Djantic pour validation du modèle Technidis"""

    uuid_identification: uuid.UUID
    supplier: str
    supplier_ident: str

    class Config:
        """Config"""

        model = EdiImport
        include = list(get_columns(ColumnDefinition, "Technidis")) + [
            "uuid_identification",
            "flow_name",
            "supplier",
            "supplier_ident",
        ]


class UnitronSchema(
    ModelSchema,
    ValidateFieldsBase,
    TvaGenerique,
):
    """Schema Djantic pour validation du modèle Unitron"""

    uuid_identification: uuid.UUID
    supplier: str
    supplier_ident: str

    class Config:
        """Config"""

        model = EdiImport
        include = list(get_columns(ColumnDefinition, "Unitron")) + [
            "uuid_identification",
            "flow_name",
            "supplier",
            "supplier_ident",
        ]


class WidexSchema(
    ModelSchema,
    ValidateFieldsBase,
    TvaWidex,
):
    """Schema Djantic pour validation du modèle Widex"""

    uuid_identification: uuid.UUID
    supplier: str
    supplier_ident: str

    class Config:
        """Config"""

        model = EdiImport
        include = list(get_columns(ColumnDefinition, "Widex")) + [
            "uuid_identification",
            "flow_name",
            "supplier",
            "supplier_ident",
        ]


class WidexGaSchema(
    ModelSchema,
    ValidateFieldsBase,
    TvaWidex,
):
    """Schema Djantic pour validation du modèle WidexGa"""

    uuid_identification: uuid.UUID
    supplier: str
    supplier_ident: str

    class Config:
        """Config"""

        model = EdiImport
        include = list(get_columns(ColumnDefinition, "WidexGa")) + [
            "uuid_identification",
            "flow_name",
            "supplier",
            "supplier_ident",
        ]
