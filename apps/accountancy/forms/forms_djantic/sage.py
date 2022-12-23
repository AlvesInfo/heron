# pylint: disable=E0401,R0903,C0115
"""
FR : Module de validation par djantic
EN : Sage X3 import validation forms module

Commentaire:

created at: 2022-02-17
created by: Paulo ALVES

modified at: 2022-02-17
modified by: Paulo ALVES
"""
import datetime
import uuid

from django.utils import timezone
from djantic import ModelSchema

from apps.core.validations.pydantic_validators_base import (
    NullZeroDecimalFieldBase,
    SageTruncateStrFieldsBase,
    SageDateFieldsBase,
    SageDefaultDateFieldsBase,
    SageNullFalseBooleanFieldsBase,
    SageNullBooleanFieldsBase,
)
from apps.accountancy.models import (
    AccountSage,
    AxeSage,
    SectionSage,
    VatRegimeSage,
    VatSage,
    VatRatSage,
    PaymentCondition,
    TabDivSage,
    CategorySage,
    CurrencySage,
)


class AccountSageSchema(ModelSchema, SageTruncateStrFieldsBase, SageNullFalseBooleanFieldsBase):
    """Schema Djantic pour validation du modèle AccountSage"""

    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now
    uuid_identification: uuid.UUID = uuid.uuid4()

    class Config:
        model = AccountSage
        include = list(model.get_columns_import()) + [
            "created_at",
            "modified_at",
            "uuid_identification",
        ]


class AxeSageSchema(ModelSchema, SageTruncateStrFieldsBase):
    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now

    class Config:
        model = AxeSage
        include = list(model.get_columns_import()) + ["created_at", "modified_at"]


class SectionSageSchema(ModelSchema, SageTruncateStrFieldsBase, SageNullFalseBooleanFieldsBase):
    chargeable: bool = None
    now = timezone.now()
    axe: str
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now
    uuid_identification: uuid.UUID = uuid.uuid4()

    class Config:
        model = SectionSage
        include = list(model.get_columns_import()) + [
            "created_at",
            "modified_at",
            "uuid_identification",
        ]


class VatRegimeSageSchema(ModelSchema, SageTruncateStrFieldsBase, SageNullFalseBooleanFieldsBase):
    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now

    class Config:
        model = VatRegimeSage
        include = list(model.get_columns_import()) + ["created_at", "modified_at"]


class VatSageSchema(ModelSchema, SageTruncateStrFieldsBase):
    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now

    class Config:
        model = VatSage
        include = list(model.get_columns_import()) + ["created_at", "modified_at"]


class VatRatSageSchema(
    ModelSchema,
    SageTruncateStrFieldsBase,
    SageDefaultDateFieldsBase,
    SageNullFalseBooleanFieldsBase,
    NullZeroDecimalFieldBase,
):
    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now
    vat: str
    exoneration: bool = None

    class Config:
        model = VatRatSage
        include = list(model.get_columns_import()) + ["created_at", "modified_at"]


class PaymentConditionSchema(ModelSchema, SageTruncateStrFieldsBase):
    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now

    class Config:
        model = PaymentCondition
        include = list(model.get_columns_import()) + ["created_at", "modified_at"]


class TabDivSageSchema(
    ModelSchema,
    SageTruncateStrFieldsBase,
    SageNullFalseBooleanFieldsBase,
    NullZeroDecimalFieldBase,
):
    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now

    class Config:
        model = TabDivSage
        include = list(model.get_columns_import()) + ["created_at", "modified_at"]


class CategorySageSchema(ModelSchema, SageTruncateStrFieldsBase):
    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now

    class Config:
        model = CategorySage
        include = list(model.get_columns_import()) + ["created_at", "modified_at"]


class CurrencySageSchema(
    ModelSchema,
    SageTruncateStrFieldsBase,
    SageDateFieldsBase,
    SageNullBooleanFieldsBase,
    NullZeroDecimalFieldBase,
):
    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now
    uuid_identification: uuid.UUID = uuid.uuid4()

    class Config:
        model = CurrencySage
        include = list(model.get_columns_import()) + [
            "created_at",
            "modified_at",
            "uuid_identification",
        ]
