from djantic import ModelSchema

from apps.edi.models import EdiImport


class EdiImportSchema(ModelSchema):
    class Config:
        model = EdiImport
