# pylint: disable=R0903,E0401,E0213
"""
FR : Module de validation par djantic des données des parametres ou data de remplissage de tables
EN : Validation module by djantic of parameter data or table filling data

Commentaire:

created at: 2023-05-13
created by: Paulo ALVES

modified at: 2023-05-13
modified by: Paulo ALVES
"""
import uuid
from typing import Union

from djantic import ModelSchema

from apps.core.validations.pydantic_validators_base import ValidateFieldsBase, validator
from apps.centers_purchasing.models import AccountsAxeProCategory


class AxeProAccountSchema(
    ModelSchema,
    ValidateFieldsBase,
):
    """Schema Djantic pour validation du modèle AccountsAxeProCategory"""

    child_center: str
    big_category: uuid.UUID
    sub_category: Union[uuid.UUID, str, None]
    axe_pro: uuid.UUID
    vat: str
    purchase_account: uuid.UUID
    sale_account: uuid.UUID
    uuid_identification: uuid.UUID

    @validator("sub_category")
    def prevent_none(cls, value):
        """Validateur pour le champ sub_category optionnel"""
        if value == "":
            return None

        return value

    class Config:
        """Config"""

        model = AccountsAxeProCategory
        include = list(AccountsAxeProCategory.get_columns_import()) + [
            "uuid_identification",
            "created_at",
            "modified_at",
        ]
