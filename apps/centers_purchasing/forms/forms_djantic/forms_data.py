# pylint: disable=R0903,E0401
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

from djantic import ModelSchema

from apps.core.validations.pydantic_validators_base import (
    ValidateFieldsBase,
)
from apps.edi.models import ColumnDefinition
from apps.edi.parameters.invoices_imports import get_columns
from apps.centers_purchasing.models import AccountsAxeProCategory


class AxeProAccountSchema(
    ModelSchema,
    ValidateFieldsBase,
):
    """Schema Djantic pour validation du modèle AccountsAxeProCategory"""

    uuid_identification: uuid.UUID

    class Config:
        """Config"""

        model = AccountsAxeProCategory
        include = list(get_columns(ColumnDefinition, "import_accounts_axe_pro_category")) + [
            "uuid_identification",
            "created_at",
            "modified_at",
        ]
