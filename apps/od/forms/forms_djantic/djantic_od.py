"""FR : Module de validation par djantic.

EN : Sage X3 import validation forms module.

Commentaire:

created at: 2025-03-15
created by: Paulo ALVES

modified at: 2025-03-15
modified by: Paulo ALVES
"""

import datetime
from typing import ClassVar

from django.utils import timezone
from djantic import ModelSchema

from apps.core.validations.djantic_compat import schema_config
from apps.core.validations.pydantic_validators_base import (
    ExcelDateFieldsBase,
    SageTruncateStrFieldsBase,
    ValidateFieldsBase,
)
from apps.od.models import ModelOd


class OdSchema(ModelSchema, ValidateFieldsBase, SageTruncateStrFieldsBase, ExcelDateFieldsBase):
    """Schema Djantic pour validation du modèle AccountSage."""

    now: ClassVar[datetime.datetime] = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now

    model_config = schema_config(
        ModelOd, include=[*ModelOd.get_columns_import(), "created_at", "modified_at"]
    )
