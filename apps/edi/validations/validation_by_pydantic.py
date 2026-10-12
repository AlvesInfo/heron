"""Schéma djantic de validation des imports EDI."""

from djantic import ModelSchema

from apps.edi.models import EdiImport


class EdiImportSchema(ModelSchema):
    """Schéma djantic des lignes d'import EDI."""

    class Config:
        """Configuration djantic : modèle et colonnes incluses dans le schéma."""

        model = EdiImport
