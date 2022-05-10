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
from djantic import ModelSchema

from apps.core.validations.pydantic_validators_base import (
    SageTruncateStrFieldsBase,
    SageNullFalseBooleanFieldsBase,
    SageDefaultDateFieldsBase,
)
from apps.countries.models import Country


class CountrySageSchema(
    ModelSchema,
    SageTruncateStrFieldsBase,
    SageNullFalseBooleanFieldsBase,
    SageDefaultDateFieldsBase,
):
    """
    Schema Djantic pour validation du modèle Country (CRY)
    Validation de l'import ZBICRY des pays Sage X3
    """

    class Config:
        """class Config du models au sens django"""

        model = Country
        include = list(Country.get_columns_import())
