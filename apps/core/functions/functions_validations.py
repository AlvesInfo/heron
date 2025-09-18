# pylint: disable=
"""Module pour validation des données à inserrer, avec des instances de
    - forms.Form et forms.ModelForm de Django
    - serializers.Serializer et serializers.ModelSerializer de DRF
    - BaseModel de Pydantic
    - ModelSchema de Djantic

Commentaire:

created at: 2021-10-30
created by: Paulo ALVES

modified at: 2021-10-30
modified by: Paulo ALVES
"""
import io
from pydantic import BaseModel, EmailStr


class CheckEmail(BaseModel):
    """Check un email par pydantic"""
    email: EmailStr


class InsertAllOrNothingTemplate:
    """
    Implémentation d'un template pour insertion total ou rien en base de données
    """

    def __init__(self, io_file: io.StringIO):
        """
        :param io_file: source des données à intégrer fichier de type io.StringIO
        """
        self.io_file = 0


class InsertDoNothingTemplate:
    """
    Implémentation d'un template pour insertion que des données valides en base de données
    """


class UpsertTemplate:
    """
    Implémentation d'un template pour upsert des données en base de données
    """


class ErrorsSaveTemplate:
    """
    Implémentation d'un template pour inserrer les données en base de données
    """


class DjangoFormErrors:
    """
    Formate la sortie des erreurs de validation pour les formulaires Django
    """

    def __init__(self, file_name: str):
        self.file_name = file_name


class DrfSerializerErrors:
    """
    Formate la sortie des erreurs de validation pour les serializers DRF
    """


class BaseModelPydanticErrors:
    """
    Formate la sortie des erreurs de validation pour les models Pydantic
    """


class ModelSchemaDjanticErrors:
    """
    Formate la sortie des erreurs de validation pour les models Schema DJantic
    """


class Validation:
    """
    Validation des modèles de données à intégrer en base
    """
