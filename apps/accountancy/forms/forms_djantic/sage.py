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

    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now
    uuid_identification: uuid.UUID = uuid.uuid4()

    class Config:
        """Configuration djantic : modèle et colonnes incluses dans le schéma."""

        model = AccountSage
        include = [*model.get_columns_import(), "created_at", "modified_at", "uuid_identification"]


class AxeSageSchema(ModelSchema, SageTruncateStrFieldsBase):
    """Schéma de validation des axes Sage."""

    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now

    class Config:
        """Configuration djantic : modèle et colonnes incluses dans le schéma."""

        model = AxeSage
        include = [*model.get_columns_import(), "created_at", "modified_at"]


class SectionSageSchema(ModelSchema, SageTruncateStrFieldsBase, SageNullFalseBooleanFieldsBase):
    """Schéma de validation des sections analytiques Sage."""

    chargeable: bool = False
    active: bool = False
    now = timezone.now()
    axe: str
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now
    uuid_identification: uuid.UUID = uuid.uuid4()
    cpy_fcy: str | None = None

    class Config:
        """Configuration djantic : modèle et colonnes incluses dans le schéma."""

        model = SectionSage
        include = [*model.get_columns_import(), "created_at", "modified_at", "uuid_identification"]


class VatRegimeSageSchema(ModelSchema, SageTruncateStrFieldsBase, SageNullFalseBooleanFieldsBase):
    """Schéma de validation des régimes de TVA Sage."""

    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now
    uuid_identification: uuid.UUID = uuid.uuid4()
    legislation: str = ""

    class Config:
        """Configuration djantic : modèle et colonnes incluses dans le schéma."""

        model = VatRegimeSage
        include = [*model.get_columns_import(), "created_at", "modified_at", "uuid_identification"]


class VatSageSchema(ModelSchema, SageTruncateStrFieldsBase):
    """Schéma de validation des codes TVA Sage."""

    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now
    auuid: uuid.UUID

    class Config:
        """Configuration djantic : modèle et colonnes incluses dans le schéma."""

        model = VatSage
        include = [*model.get_columns_import(), "created_at", "modified_at"]


class VatRatSageSchema(
    ModelSchema,
    SageTruncateStrFieldsBase,
    SageDefaultDateFieldsBase,
    SageNullFalseBooleanFieldsBase,
    NullZeroDecimalFieldBase,
):
    """Schéma de validation des taux de TVA Sage."""

    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now
    vat: str
    exoneration: bool = False
    auuid: uuid.UUID

    class Config:
        """Configuration djantic : modèle et colonnes incluses dans le schéma."""

        model = VatRatSage
        include = [*model.get_columns_import(), "created_at", "modified_at"]


class ModeReglementSchema(ModelSchema, SageTruncateStrFieldsBase):
    """Schéma de validation des modes de règlement Sage."""

    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now

    class Config:
        """Configuration djantic : modèle et colonnes incluses dans le schéma."""

        model = ModeReglement
        include = [*model.get_columns_import(), "created_at", "modified_at"]


class PaymentConditionSchema(ModelSchema, SageTruncateStrFieldsBase):
    """Schéma de validation des conditions de paiement Sage."""

    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now

    class Config:
        """Configuration djantic : modèle et colonnes incluses dans le schéma."""

        model = PaymentCondition
        include = [*model.get_columns_import(), "created_at", "modified_at"]


class TabDivSageSchema(
    ModelSchema,
    SageTruncateStrFieldsBase,
    SageNullFalseBooleanFieldsBase,
    NullZeroDecimalFieldBase,
):
    """Schéma de validation des tables diverses Sage."""

    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now

    class Config:
        """Configuration djantic : modèle et colonnes incluses dans le schéma."""

        model = TabDivSage
        include = [*model.get_columns_import(), "created_at", "modified_at"]


class CategorySageSchema(ModelSchema, SageTruncateStrFieldsBase):
    """Schéma de validation des catégories Sage."""

    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now

    class Config:
        """Configuration djantic : modèle et colonnes incluses dans le schéma."""

        model = CategorySage
        include = [*model.get_columns_import(), "created_at", "modified_at"]


class CurrencySageSchema(
    ModelSchema,
    SageTruncateStrFieldsBase,
    SageDateFieldsBase,
    SageNullBooleanFieldsBase,
    NullZeroDecimalFieldBase,
):
    """Schéma de validation des devises Sage."""

    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now
    uuid_identification: uuid.UUID = uuid.uuid4()

    class Config:
        """Configuration djantic : modèle et colonnes incluses dans le schéma."""

        model = CurrencySage
        include = [*model.get_columns_import(), "created_at", "modified_at", "uuid_identification"]
