# pylint: disable=E0401,R0903
"""
FR : Module de validation par djantic
EN : Sage X3 import validation forms module

Commentaire:

created at: 2022-05-10
created by: Paulo ALVES

modified at: 2022-05-10
modified by: Paulo ALVES
"""
import datetime
import uuid

from django.utils import timezone
from djantic import ModelSchema

from apps.core.validations.pydantic_validators_base import (
    SageTruncateStrFieldsBase,
    SageNullFalseBooleanFieldsBase,
)
from apps.book.models import (
    BprBookSage,
    BpsBookSage,
    BpcBookSage,
    BookAdressesSage,
    CodeContactsSage,
    BookContactsSage,
    BookBanksSage,
)


class BprBookSageSchema(ModelSchema, SageTruncateStrFieldsBase, SageNullFalseBooleanFieldsBase):
    """
    Schema Djantic pour validation du modèle Society (BPR)
    Validation de l'import ZBIBPR des Tiers Génériques Sage X3
    """

    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now
    country: str

    class Config:
        """class Config du models au sens django"""

        base_model = BprBookSage
        model = base_model.model
        include = list(base_model.get_columns_import()) + [
            "created_at",
            "modified_at",
        ]


class BpsBookSageSchema(ModelSchema, SageTruncateStrFieldsBase, SageNullFalseBooleanFieldsBase):
    """
    Schema Djantic pour validation du modèle Society (BPS)
    Validation de l'import ZBIBPS des Tiers Génériques Sage X3
    """

    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now

    class Config:
        """class Config du models au sens django"""

        base_model = BpsBookSage
        model = base_model.model
        include = list(base_model.get_columns_import()) + [
            "created_at",
            "modified_at",
        ]


class BpcBookSageSchema(ModelSchema, SageTruncateStrFieldsBase, SageNullFalseBooleanFieldsBase):
    """
    Schema Djantic pour validation du modèle Society (BPC)
    Validation de l'import ZBIBPC des Tiers Génériques Sage X3
    """

    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now

    class Config:
        """class Config du models au sens django"""

        base_model = BpcBookSage
        model = base_model.model
        include = list(base_model.get_columns_import()) + [
            "created_at",
            "modified_at",
        ]


class BookAdressesSageSchema(
    ModelSchema, SageTruncateStrFieldsBase, SageNullFalseBooleanFieldsBase
):
    """
    Schema Djantic pour validation du modèle Society-Adress
    Validation de l'import ZBIADDR des Tiers Génériques Sage X3
    """

    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now
    society: str
    country: str

    class Config:
        """class Config du models au sens django"""

        base_model = BookAdressesSage
        model = base_model.model
        include = list(base_model.get_columns_import()) + [
            "created_at",
            "modified_at",
        ]


class CodeContactsSageSchema(
    ModelSchema, SageTruncateStrFieldsBase, SageNullFalseBooleanFieldsBase
):
    """
    Schema Djantic pour validation du modèle Society-Code-Contact
    Validation de l'import ZBICONTACT des Tiers Génériques Sage X3
    """

    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now
    uuid_identification: uuid.UUID = uuid.uuid4()
    society: str
    country: str

    class Config:
        """class Config du models au sens django"""

        base_model = CodeContactsSage
        model = base_model.model
        include = list(base_model.get_columns_import()) + [
            "created_at",
            "modified_at",
            "uuid_identification",
        ]


class BookContactsSageSchema(
    ModelSchema, SageTruncateStrFieldsBase, SageNullFalseBooleanFieldsBase
):
    """
    Schema Djantic pour validation du modèle Society-Contact
    Validation de l'import ZBICONTCRM des Tiers Génériques Sage X3
    """

    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now
    uuid_identification: uuid.UUID = uuid.uuid4()
    society: str
    country: str

    class Config:
        """class Config du models au sens django"""

        base_model = BookContactsSage
        model = base_model.model
        include = list(base_model.get_columns_import()) + [
            "created_at",
            "modified_at",
            "uuid_identification",
        ]


class BookBanksSageSchema(ModelSchema, SageTruncateStrFieldsBase, SageNullFalseBooleanFieldsBase):
    """
    Schema Djantic pour validation du modèle Society-Contact
    Validation de l'import ZBIBANK des Tiers Génériques Sage X3
    """

    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now
    society: str
    country: str

    class Config:
        """class Config du models au sens django"""

        base_model = BookBanksSage
        model = base_model.model
        include = list(base_model.get_columns_import()) + [
            "created_at",
            "modified_at",
        ]
