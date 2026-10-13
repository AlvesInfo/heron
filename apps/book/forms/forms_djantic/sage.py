"""FR : Module de validation par djantic.

EN : Sage X3 import validation forms module.

Commentaire:

created at: 2022-05-10
created by: Paulo ALVES

modified at: 2022-05-10
modified by: Paulo ALVES
"""

import datetime
import uuid
from typing import ClassVar

from django.utils import timezone
from djantic import ModelSchema

from apps.book.models import (
    BookAdressesSage,
    BookBanksSage,
    BookContactsSage,
    BpcBookSage,
    BprBookSage,
    BpsBookSage,
    CodeContactsSage,
)
from apps.core.validations.djantic_compat import schema_config
from apps.core.validations.pydantic_validators_base import (
    SageNullFalseBooleanFieldsBase,
    SageTruncateStrFieldsBase,
)


class BprBookSageSchema(ModelSchema, SageTruncateStrFieldsBase, SageNullFalseBooleanFieldsBase):
    """Schema Djantic pour validation du modèle Society (BPR).

    Validation de l'import ZBIBPR des Tiers Génériques Sage X3.
    """

    now: ClassVar[datetime.datetime] = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now
    country: str

    model_config = schema_config(
        BprBookSage.model, include=[*BprBookSage.get_columns_import(), "created_at", "modified_at"]
    )


class BpsBookSageSchema(ModelSchema, SageTruncateStrFieldsBase, SageNullFalseBooleanFieldsBase):
    """Schema Djantic pour validation du modèle Society (BPS).

    Validation de l'import ZBIBPS des Tiers Génériques Sage X3.
    """

    now: ClassVar[datetime.datetime] = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now
    payment_condition_supplier: str

    model_config = schema_config(
        BpsBookSage.model, include=[*BpsBookSage.get_columns_import(), "created_at", "modified_at"]
    )


class BpcBookSageSchema(ModelSchema, SageTruncateStrFieldsBase, SageNullFalseBooleanFieldsBase):
    """Schema Djantic pour validation du modèle Society (BPC).

    Validation de l'import ZBIBPC des Tiers Génériques Sage X3.
    """

    now: ClassVar[datetime.datetime] = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now
    payment_condition_client: str

    model_config = schema_config(
        BpcBookSage.model, include=[*BpcBookSage.get_columns_import(), "created_at", "modified_at"]
    )


class BookAdressesSageSchema(
    ModelSchema, SageTruncateStrFieldsBase, SageNullFalseBooleanFieldsBase
):
    """Schema Djantic pour validation du modèle Society-Adress.

    Validation de l'import ZBIADDR des Tiers Génériques Sage X3.
    """

    now: ClassVar[datetime.datetime] = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now
    society: str
    country: str

    model_config = schema_config(
        BookAdressesSage.model,
        include=[*BookAdressesSage.get_columns_import(), "created_at", "modified_at"],
    )


class CodeContactsSageSchema(
    ModelSchema, SageTruncateStrFieldsBase, SageNullFalseBooleanFieldsBase
):
    """Schema Djantic pour validation du modèle Society-Code-Contact.

    Validation de l'import ZBICONTACT des Tiers Génériques Sage X3.
    """

    now: ClassVar[datetime.datetime] = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now
    uuid_identification: uuid.UUID = uuid.uuid4()
    society: str

    model_config = schema_config(
        CodeContactsSage.model,
        include=[
            *CodeContactsSage.get_columns_import(),
            "created_at",
            "modified_at",
            "uuid_identification",
        ],
    )


class BookContactsSageSchema(
    ModelSchema, SageTruncateStrFieldsBase, SageNullFalseBooleanFieldsBase
):
    """Schema Djantic pour validation du modèle Society-Contact.

    Validation de l'import ZBICONTCRM des Tiers Génériques Sage X3.
    """

    now: ClassVar[datetime.datetime] = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now
    uuid_identification: uuid.UUID = uuid.uuid4()
    society: str
    country: str

    model_config = schema_config(
        BookContactsSage.model,
        include=[
            *BookContactsSage.get_columns_import(),
            "created_at",
            "modified_at",
            "uuid_identification",
        ],
    )


class BookBanksSageSchema(ModelSchema, SageTruncateStrFieldsBase, SageNullFalseBooleanFieldsBase):
    """Schema Djantic pour validation du modèle Society-Contact.

    Validation de l'import ZBIBANK des Tiers Génériques Sage X3.
    """

    now: ClassVar[datetime.datetime] = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now
    society: str
    country: str

    model_config = schema_config(
        BookBanksSage.model,
        include=[*BookBanksSage.get_columns_import(), "created_at", "modified_at"],
    )
