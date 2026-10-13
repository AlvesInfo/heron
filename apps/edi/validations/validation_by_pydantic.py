"""Schéma djantic de validation des imports EDI."""

from djantic import ModelSchema

from apps.core.validations.djantic_compat import schema_config
from apps.edi.models import EdiImport


class EdiImportSchema(ModelSchema):
    """Schéma djantic des lignes d'import EDI."""

    model_config = schema_config(EdiImport)
