"""FR : Module de validation par djantic des souscription des abonnements par maisons.

EN : Djantic validation module for subscription subscriptions by houses.

Commentaire:

created at: 2024-03-31
created by: Paulo ALVES

modified at: 2024-03-31
modified by: Paulo ALVES
"""

import datetime
from uuid import UUID

from django.utils import timezone
from djantic import ModelSchema

from apps.centers_clients.models import MaisonSubcription


class MaisonSubcriptionSchema(ModelSchema):
    """Schema Djantic pour validation du modèle MaisonSubcription."""

    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now
    maison: str
    article: UUID
    unit_weight: int
    function: str
    for_signboard: str
    vat: str | None = None

    class Config:
        """Configuration djantic : modèle et colonnes incluses dans le schéma."""

        model = MaisonSubcription
        include = [*model.get_columns_import(), "created_at", "modified_at"]
