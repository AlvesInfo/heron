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
import uuid
from typing import Any, AnyStr, Dict, Iterable

import redis
from pydantic import BaseModel
from djantic import ModelSchema
from rest_framework import serializers
from django.db import models
from django import forms

from apps.core.functions.functions_setups import settings


try:
    CACHE = redis.StrictRedis(
        host=settings.REDIS_HOST, port=settings.REDIS_PORT, password=settings.REDIS_PASSWORD
    )
except redis.exceptions.ConnectionError:
    CACHE = None


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


class ValidationFactoryTemplate:
    """Template de validation"""

    def __init__(
        self,
        validator: [
            BaseModel,
            ModelSchema,
            serializers.Serializer,
            serializers.ModelSerializer,
            forms.Form,
            forms.ModelForm,
        ],
        elements: Iterable[Any],
        io_file: io.StringIO,
        nb_errors: int = 99_000,
    ):
        """Initialisation de ValidationTemplate"""
        self.validator = validator
        self.elements = elements
        self.io_file = io_file
        self.nb_errors = nb_errors

        self.io_file.seek(0)

    def is_valid(self):
        """
        Validation des données la méthode is_valid doit retourner
               (S'il y a des Erreurs)   (L'id des messages d'erreur)
        return     True or false      ,
        """
        raise NotImplementedError

    def validate(self):
        """Lancement de la validation"""
        self.io_file.seek(0)
        return self.is_valid()


class DjangoValidation(ValidationFactoryTemplate):
    """Validation par les formulaires django"""

    def is_valid(self):
        """Lancement de la validation"""


class Validation:
    """
    Validation des modèles de données à intégrer en base
    """

    def __init__(
        self,
        flow_name: AnyStr,
        model: models.Model,
        validator: [
            BaseModel,
            ModelSchema,
            serializers.Serializer,
            serializers.ModelSerializer,
            forms.Form,
            forms.ModelForm,
        ],
        params_dict: Dict = None,
    ):
        """
        initialisation de la classe
        :param flow_name:
        :param model:
        :param validator:
        :param params_dict: Dictionnaire des paramètres :
                                params_dict = {

                                }
        """
        self.params_dict = params_dict or {}


if __name__ == "__main__":

    CACHE.set("t", "test")
    print(CACHE.get("t"))
    uuid = str(uuid.uuid4())
    print(uuid)
    CACHE.set(uuid, "errors")
    print(CACHE.get(uuid))
