"""FR : Module de validation par djantic.

EN : Sage X3 import validation forms module.

Commentaire:

created at: 2022-02-17
created by: Paulo ALVES

modified at: 2022-02-17
modified by: Paulo ALVES
"""

import datetime
import uuid
from typing import ClassVar

from django.utils import timezone
from djantic import ModelSchema

from apps.accountancy.models import (
    AccountSage,
    AxeSage,
    CategorySage,
    CurrencySage,
    ModeReglement,
    PaymentCondition,
    SectionSage,
    TabDivSage,
    VatRatSage,
    VatRegimeSage,
    VatSage,
)
from apps.core.validations.djantic_compat import schema_config
from apps.core.validations.pydantic_validators_base import (
    NullZeroDecimalFieldBase,
    SageDateFieldsBase,
    SageDefaultDateFieldsBase,
    SageNullBooleanFieldsBase,
    SageNullFalseBooleanFieldsBase,
    SageTruncateStrFieldsBase,
)


class AccountSageSchema(ModelSchema, SageTruncateStrFieldsBase, SageNullFalseBooleanFieldsBase):
    """Schema Djantic pour validation du modèle AccountSage."""

    now: ClassVar[datetime.datetime] = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now
    uuid_identification: uuid.UUID = uuid.uuid4()

    model_config = schema_config(
        AccountSage,
        include=[
            *AccountSage.get_columns_import(),
            "created_at",
            "modified_at",
            "uuid_identification",
        ],
    )


class AxeSageSchema(ModelSchema, SageTruncateStrFieldsBase):
    """Schéma de validation des axes Sage."""

    now: ClassVar[datetime.datetime] = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now

    model_config = schema_config(
        AxeSage, include=[*AxeSage.get_columns_import(), "created_at", "modified_at"]
    )


class SectionSageSchema(ModelSchema, SageTruncateStrFieldsBase, SageNullFalseBooleanFieldsBase):
    """Schéma de validation des sections analytiques Sage."""

    chargeable: bool = False
    active: bool = False
    now: ClassVar[datetime.datetime] = timezone.now()
    axe: str
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now
    uuid_identification: uuid.UUID = uuid.uuid4()
    cpy_fcy: str | None = None

    model_config = schema_config(
        SectionSage,
        include=[
            *SectionSage.get_columns_import(),
            "created_at",
            "modified_at",
            "uuid_identification",
        ],
    )


class VatRegimeSageSchema(ModelSchema, SageTruncateStrFieldsBase, SageNullFalseBooleanFieldsBase):
    """Schéma de validation des régimes de TVA Sage."""

    now: ClassVar[datetime.datetime] = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now
    uuid_identification: uuid.UUID = uuid.uuid4()
    legislation: str = ""

    model_config = schema_config(
        VatRegimeSage,
        include=[
            *VatRegimeSage.get_columns_import(),
            "created_at",
            "modified_at",
            "uuid_identification",
        ],
    )


class VatSageSchema(ModelSchema, SageTruncateStrFieldsBase):
    """Schéma de validation des codes TVA Sage."""

    now: ClassVar[datetime.datetime] = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now
    auuid: uuid.UUID

    model_config = schema_config(
        VatSage, include=[*VatSage.get_columns_import(), "created_at", "modified_at"]
    )


class VatRatSageSchema(
    ModelSchema,
    SageTruncateStrFieldsBase,
    SageDefaultDateFieldsBase,
    SageNullFalseBooleanFieldsBase,
    NullZeroDecimalFieldBase,
):
    """Schéma de validation des taux de TVA Sage."""

    now: ClassVar[datetime.datetime] = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now
    vat: str
    exoneration: bool = False
    auuid: uuid.UUID

    model_config = schema_config(
        VatRatSage, include=[*VatRatSage.get_columns_import(), "created_at", "modified_at"]
    )


class ModeReglementSchema(ModelSchema, SageTruncateStrFieldsBase):
    """Schéma de validation des modes de règlement Sage."""

    now: ClassVar[datetime.datetime] = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now

    model_config = schema_config(
        ModeReglement, include=[*ModeReglement.get_columns_import(), "created_at", "modified_at"]
    )


class PaymentConditionSchema(ModelSchema, SageTruncateStrFieldsBase):
    """Schéma de validation des conditions de paiement Sage."""

    now: ClassVar[datetime.datetime] = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now

    model_config = schema_config(
        PaymentCondition,
        include=[*PaymentCondition.get_columns_import(), "created_at", "modified_at"],
    )


class TabDivSageSchema(
    ModelSchema,
    SageTruncateStrFieldsBase,
    SageNullFalseBooleanFieldsBase,
    NullZeroDecimalFieldBase,
):
    """Schéma de validation des tables diverses Sage."""

    now: ClassVar[datetime.datetime] = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now

    model_config = schema_config(
        TabDivSage, include=[*TabDivSage.get_columns_import(), "created_at", "modified_at"]
    )


class CategorySageSchema(ModelSchema, SageTruncateStrFieldsBase):
    """Schéma de validation des catégories Sage."""

    now: ClassVar[datetime.datetime] = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now

    model_config = schema_config(
        CategorySage, include=[*CategorySage.get_columns_import(), "created_at", "modified_at"]
    )


class CurrencySageSchema(
    ModelSchema,
    SageTruncateStrFieldsBase,
    SageDateFieldsBase,
    SageNullBooleanFieldsBase,
    NullZeroDecimalFieldBase,
):
    """Schéma de validation des devises Sage."""

    now: ClassVar[datetime.datetime] = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now
    uuid_identification: uuid.UUID = uuid.uuid4()

    model_config = schema_config(
        CurrencySage,
        include=[
            *CurrencySage.get_columns_import(),
            "created_at",
            "modified_at",
            "uuid_identification",
        ],
    )
