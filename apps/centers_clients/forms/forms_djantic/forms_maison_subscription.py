"""FR : Module de validation par djantic des souscription des abonnements par maisons.

EN : Djantic validation module for subscription subscriptions by houses.

Commentaire:

created at: 2024-03-31
created by: Paulo ALVES

modified at: 2024-03-31
modified by: Paulo ALVES
"""

import datetime
from typing import ClassVar
from uuid import UUID

from django.utils import timezone
from djantic import ModelSchema

from apps.centers_clients.models import MaisonSubcription
from apps.core.validations.djantic_compat import schema_config


class MaisonSubcriptionSchema(ModelSchema):
    """Schema Djantic pour validation du modèle MaisonSubcription."""

    now: ClassVar[datetime.datetime] = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now
    maison: str
    article: UUID
    unit_weight: int
    function: str
    for_signboard: str
    vat: str | None = None

    model_config = schema_config(
        MaisonSubcription,
        include=[*MaisonSubcription.get_columns_import(), "created_at", "modified_at"],
    )
