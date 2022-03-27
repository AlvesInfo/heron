# pylint: disable=E0401
"""Module de validation des flux à intégrer en BDD

Instances de validation implémentées :
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
