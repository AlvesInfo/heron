"""FR : Module de validation par djantic des données des parametres ou data de remplissage de tables.

EN : Validation module by djantic of parameter data or table filling data.

Commentaire:

created at: 2023-05-13
created by: Paulo ALVES

modified at: 2023-05-13
modified by: Paulo ALVES
"""

import uuid

from djantic import ModelSchema
from pydantic import Field

from apps.centers_purchasing.models import AccountsAxeProCategory
from apps.core.validations.djantic_compat import schema_config
from apps.core.validations.pydantic_validators_base import ValidateFieldsBase, field_validator


class AxeProAccountSchema(
    ModelSchema,
    ValidateFieldsBase,
):
    """Schema Djantic pour validation du modèle AccountsAxeProCategory."""

    child_center: str
    big_category: uuid.UUID
    # union_mode : pydantic 2 garderait le texte, l'UUID doit être tenté en premier (pydantic 1)
    sub_category: uuid.UUID | str | None = Field(default=None, union_mode="left_to_right")
    axe_pro: uuid.UUID
    vat: str
    purchase_account: uuid.UUID
    sale_account: uuid.UUID
    uuid_identification: uuid.UUID

    @field_validator("sub_category")
    @classmethod
    def prevent_none(cls, value):
        """Validateur pour le champ sub_category optionnel."""
        if value == "":
            return None

        return value

    model_config = schema_config(
        AccountsAxeProCategory,
        include=[
            *AccountsAxeProCategory.get_columns_import(),
            "uuid_identification",
            "created_at",
            "modified_at",
        ],
    )
