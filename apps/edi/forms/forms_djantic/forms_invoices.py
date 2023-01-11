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
import datetime

from djantic import ModelSchema
from pydantic import validator

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


class BbgrBulkSchema(
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
        include = list(get_columns(ColumnDefinition, "BbgrBulk")) + [
            "uuid_identification",
            "flow_name",
            "supplier",
            "supplier_ident",
            "created_at",
            "modified_at",
        ]


class CosiumSchema(
    ModelSchema,
    ValidateFieldsBase,
    TvaWidex,
):
    """Schema Djantic pour validation du modèle BbrgVerre"""

    uuid_identification: uuid.UUID

    class Config:
        """Config"""

        model = EdiImport
        include = list(get_columns(ColumnDefinition, "Cosium")) + [
            "uuid_identification",
            "created_at",
            "modified_at",
        ]


class EdiSchema(
    ModelSchema,
    ValidateFieldsBase,
):
    """Schema Djantic pour validation du modèle Edi"""

    uuid_identification: uuid.UUID
    qty: Decimal = 1
    acuitis_order_date: datetime.datetime
    delivery_date: datetime.datetime

    @validator('acuitis_order_date', pre=True)
    def check_acuitis_order_date(cls, value):

        if not value or value == "None":
            return datetime.datetime(1900, 1, 1)

        return value

    @validator('delivery_date', pre=True)
    def check_delivery_date(cls, value):

        if not value or value == "None":
            return datetime.datetime(1900, 1, 1)

        return value

    class Config:
        """Config"""

        model = EdiImport
        include = list(get_columns(ColumnDefinition, "Edi")) + [
            "uuid_identification",
            "flow_name",
            "created_at",
            "modified_at",
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
            "created_at",
            "modified_at",
        ]


class GeneriqueSchema(
    ModelSchema,
    ValidateFieldsBase,
    TvaGenerique,
):
    """Schema Djantic pour validation du modèle Generique"""

    uuid_identification: uuid.UUID
    acuitis_order_date: datetime.datetime
    delivery_date: datetime.datetime

    @validator('acuitis_order_date', pre=True)
    def check_acuitis_order_date(cls, value):

        if not value or value == "None":
            return datetime.datetime(1900, 1, 1)

        return value

    @validator('delivery_date', pre=True)
    def check_delivery_date(cls, value):

        if not value or value == "None":
            return datetime.datetime(1900, 1, 1)

        return value

    class Config:
        """Config"""

        model = EdiImport
        include = list(get_columns(ColumnDefinition, "Generique")) + [
            "uuid_identification",
            "flow_name",
            "created_at",
            "modified_at",
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
            "created_at",
            "modified_at",
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
            "created_at",
            "modified_at",
        ]


class JohnsonSchema(
    ModelSchema,
    ValidateFieldsBase,
):
    """Schema Djantic pour validation du modèle Johnson"""

    uuid_identification: uuid.UUID
    supplier: str
    supplier_ident: str
    delivery_date: datetime.datetime

    @validator('delivery_date', pre=True)
    def check_delivery_date(cls, value):

        if not value or value == "None":
            return datetime.datetime(1900, 1, 1)

        return value

    class Config:
        """Config"""

        model = EdiImport
        include = list(get_columns(ColumnDefinition, "Johnson")) + [
            "uuid_identification",
            "flow_name",
            "supplier",
            "supplier_ident",
            "created_at",
            "modified_at",
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
            "created_at",
            "modified_at",
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
            "created_at",
            "modified_at",
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
            "created_at",
            "modified_at",
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
            "created_at",
            "modified_at",
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
    delivery_date: datetime.datetime

    @validator('delivery_date', pre=True)
    def check_delivery_date(cls, value):

        if not value or value == "None":
            return datetime.datetime(1900, 1, 1)

        return value

    class Config:
        """Config"""

        model = EdiImport
        include = list(get_columns(ColumnDefinition, "Signia")) + [
            "uuid_identification",
            "flow_name",
            "supplier",
            "supplier_ident",
            "created_at",
            "modified_at",
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
    delivery_date: datetime.datetime

    @validator('delivery_date', pre=True)
    def check_delivery_date(cls, value):

        if not value or value == "None":
            return datetime.datetime(1900, 1, 1)

        return value

    class Config:
        """Config"""

        model = EdiImport
        include = list(get_columns(ColumnDefinition, "Starkey")) + [
            "uuid_identification",
            "flow_name",
            "supplier",
            "supplier_ident",
            "created_at",
            "modified_at",
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
            "created_at",
            "modified_at",
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
            "created_at",
            "modified_at",
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
            "created_at",
            "modified_at",
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
            "created_at",
            "modified_at",
        ]


def main():
    class EdiEssais(ModelSchema):
        class Config:
            """Config"""

            model = EdiImport
            include = ["uuid_identification", "invoice_date"]

    try:
        data = {"uuid_identification": uuid.uuid4(), "invoice_date": "2060-12-22"}
        # noinspection PyArgumentList
        essais = EdiEssais(**data)
        print(essais.dict())
    except Exception as error:
        print(error)
