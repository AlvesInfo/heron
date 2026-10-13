"""FR : Module de validation par djantic des articles sans comptes.

EN : Djantic validation module for articles without accounts.

Commentaire:

created at: 2024-02-14
created by: Paulo ALVES

modified at: 2024-02-14
modified by: Paulo ALVES
"""

import datetime
import uuid
from typing import ClassVar

from django.utils import timezone
from djantic import ModelSchema

from apps.articles.models import ArticleAccount
from apps.core.validations.djantic_compat import schema_config


class ArticleAccountSageSchema(ModelSchema):
    """Schema Djantic pour validation du modèle AccountSage."""

    now: ClassVar[datetime.datetime] = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now
    article: uuid.UUID
    child_center: str
    vat: str

    model_config = schema_config(
        ArticleAccount, include=[*ArticleAccount.get_columns_import(), "created_at", "modified_at"]
    )
