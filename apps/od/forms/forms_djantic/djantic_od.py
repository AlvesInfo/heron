# pylint: disable=E0401,R0903,C0115
"""
FR : Module de validation par djantic
EN : Sage X3 import validation forms module

Commentaire:

created at: 2025-03-15
created by: Paulo ALVES

modified at: 2025-03-15
modified by: Paulo ALVES
"""

import datetime

from django.utils import timezone
from djantic import ModelSchema

from apps.core.validations.pydantic_validators_base import (
    ValidateFieldsBase,
    SageTruncateStrFieldsBase,
    ExcelDateFieldsBase,
)
from apps.od.models import ModelOd


class OdSchema(
    ModelSchema, ValidateFieldsBase, SageTruncateStrFieldsBase, ExcelDateFieldsBase
):
    """Schema Djantic pour validation du modèle AccountSage"""

    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now

    class Config:
        model = ModelOd
        include = list(model.get_columns_import()) + [
            "created_at",
            "modified_at",
        ]
