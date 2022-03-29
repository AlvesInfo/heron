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
from itertools import chain
import uuid
from typing import Dict, Iterable
from pydantic import BaseModel
from djantic import ModelSchema
from rest_framework import serializers as seria

from django.db import models, connection
from django import forms

from cache import CacheRegistry

# noinspection PyCompatibility
from exceptions import ValidationErrors


class FormErrorsTemplate:
    """
    Implémentation d'un template pour inserrer les données en base de données
    """

    def __init__(self, flow_name: str):
        """
        :param flow_name:
        """
        self.flow_name = flow_name
        self.registry = CacheRegistry()

    def initialize(self):
        """Initialisation du flow de l'instance self.registry"""
        # TODO : Implémenter la méthode initialize de la class FormErrorsTemplate

    def error_format(self, line, error):
        """
        Formatage de l'error passée en paramètre
        :param line: Ligne sur laquelle est arrivée l'erreur
        :param error: erreur arrivée du validateur
        :return: line, error format
        """
        raise NotImplementedError

    def add_error(self, line, error):
        """
        Ajoute une erreur à l'instance self.errors_instance
        :param line: N° de ligne traitée
        :param error: erreur sur la ligne concernée
        """
        # TODO : Implémenter la méthode add_error de la class FormErrorsTemplate

    def save(self):
        """Sauvegarde de l'intégralité des erreurs en base"""


class DjangoFormErrors(FormErrorsTemplate):
    """
    Formate la sortie des erreurs de validation pour les formulaires Django
    """

    def error_format(self, line, error):
        """
        Formatage de l'error passée en paramètre
        :param line: Ligne sur laquelle est arrivée l'erreur
        :param error: erreur arrivée du validateur
        :return: line, error format
        """


class DrfFormErrors(FormErrorsTemplate):
    """
    Formate la sortie des erreurs de validation pour les serializers DRF
    """

    def error_format(self, line, error):
        """
        Formatage de l'error passée en paramètre
        :param line: Ligne sur laquelle est arrivée l'erreur
        :param error: erreur arrivée du validateur
        :return: line, error format
        """


class PydanticFormErrors(FormErrorsTemplate):
    """
    Formate la sortie des erreurs de validation pour les models Pydantic
    """

    def error_format(self, line, error):
        """
        Formatage de l'error passée en paramètre
        :param line: Ligne sur laquelle est arrivée l'erreur
        :param error: erreur arrivée du validateur
        :return: line, error format
        """


class ValidationTemplate:
    """Template de validation"""

    def __init__(
        self,
        validators: [
            [
                BaseModel,
                ModelSchema,
                seria.Serializer,
                seria.ModelSerializer,
                forms.Form,
                forms.ModelForm,
            ],
            FormErrorsTemplate,
        ],
        dict_flow: Dict,
        params_dict: Dict,
    ):
        """
        :param validators:  Tuple formé d'un Form Validateur et de la class Errors du Validateur
        :param dict_flow:   Itérable de dict, pour validation par **kwargs
        :param params_dict: Dictionnaire des paramètres :
                                params_dict = {
                                    # Nom du flux pour le nommage des erreurs du fichier, api, ...
                                    "flow_name": "flow_name",

                                    # Nombre d'erreurs maximum avant arrêt de la validation
                                    "nb_errors_max": 100,

                                    # Methode d'insertion en base des données une fois validées
                                    "insert_method":
                                                        # jeux de données non sauvegardé,
                                                        # dès la première erreur
                                                        "insert"

                                                        # Sauvegarde par do_nothing,
                                                        # ne fait rien en cas d'erreur
                                                        "do_nothing"

                                                        # Sauvegarde par upsert,
                                                        # update ligne à ligne
                                                        "upsert"

                                    # Foreign Keys, pour validation des clés étrangères
                                    "foreign_key": ("attr_01", "attr_01", ....)
                                }
        """
        self.validator_class, self.errors_class = validators
        self.flow_name = params_dict.get("flow_name")
        self.errors_instance = self.errors_class(self.flow_name)
        self.dict_flow = dict_flow
        self.first_element = next(dict_flow)
        self.errors_instance.initialize()

    def _add_error(self, line, error):
        """
        Ajoute une erreur à l'instance self.errors_instance
        :param line: N° de ligne traitée
        :param error: erreur sur la ligne concernée
        """
        self.errors_instance.add_error(line, error)

    def _save_errors_trace(self, cursor):
        """
        Retourne l'instance des erreurs
        :param cursor: cursor de connexion à la BDD Postgresql du Projet
        """
        self.errors_instance.save(cursor)

    def is_valid(self, datas, cursor):
        """
        Validation des données par la méthode is_valid
        :param datas: Données à valider
        :param cursor: cursor de connexion à la BDD Postgresql du Projet
        :return: (Bool errors), "texte pour affichage éventuel"
        """
        raise NotImplementedError

    def validate(self):
        """Lancement de la validation"""
        if not isinstance(self.first_element, (dict,)):
            raise ValidationErrors(
                "La validation ne peut avoir lieu car le flux des données, "
                "doit être un flux de dictionnaire"
            )
        try:
            with connection.cursor() as cursor:
                errors_bool, validation_text = self.is_valid(
                    chain([self.first_element], self.dict_flow), cursor
                )
                self._save_errors_trace(cursor)
                return errors_bool, validation_text
        except Exception as error:
            raise ValidationErrors("Une erreur c'est produite à l'appel de validate") from error


class DjangoValidation(ValidationTemplate):
    """Validation par les formulaires django"""

    def __init__(
        self,
        validators: [
            [
                BaseModel,
                ModelSchema,
                seria.Serializer,
                seria.ModelSerializer,
                forms.Form,
                forms.ModelForm,
            ],
            FormErrorsTemplate,
        ],
        dict_flow: Dict,
        params_dict: Dict,
    ):
        """
        :param validators:  Tuple formé d'un Form Validateur et de la class Errors du Validateur
        :param dict_flow:   Itérable de dict, pour validation par **kwargs
        :param params_dict: Dictionnaire des paramètres :
                                params_dict = {
                                    # Nom du flux pour le nommage des erreurs du fichier, api, ...
                                    "flow_name": "flow_name",

                                    # Nombre d'erreurs maximum avant arrêt de la validation
                                    "nb_errors_max": 100,

                                    # Methode d'insertion en base des données une fois validées
                                    "insert_method":
                                                        # jeux de données non sauvegardé,
                                                        # dès la première erreur
                                                        "insert"

                                                        # Sauvegarde par do_nothing,
                                                        # ne fait rien en cas d'erreur
                                                        "do_nothing"

                                                        # Sauvegarde par upsert,
                                                        # update ligne à ligne
                                                        "upsert"

                                    # Foreign Keys, pour validation des clés étrangères
                                    "foreign_key": ("attr_01", "attr_01", ....)
                                }
        """
        super().__init__(validators, dict_flow, params_dict)
        self.nb_errors_max = params_dict.get("nb_errors_max")
        self.insert_method = params_dict.get("insert_method")
        self.foreign_key = params_dict.get("foreign_key", tuple())

    def is_valid(self, datas, cursor):
        """Lancement de la validation"""


class DrfValidation(ValidationTemplate):
    """Validation par les formulaires de seririalisation Django Rest Framework"""

    def __init__(
        self,
        validators: [
            [
                BaseModel,
                ModelSchema,
                seria.Serializer,
                seria.ModelSerializer,
                forms.Form,
                forms.ModelForm,
            ],
            FormErrorsTemplate,
        ],
        dict_flow: Dict,
        params_dict: Dict,
    ):
        """
        :param validators:  Tuple formé d'un Form Validateur et de la class Errors du Validateur
        :param dict_flow:   Itérable de dict, pour validation par **kwargs
        :param params_dict: Dictionnaire des paramètres :
                                params_dict = {
                                    # Nom du flux pour le nommage des erreurs du fichier, api, ...
                                    "flow_name": "flow_name",

                                    # Nombre d'erreurs maximum avant arrêt de la validation
                                    "nb_errors_max": 100,

                                    # Methode d'insertion en base des données une fois validées
                                    "insert_method":
                                                        # jeux de données non sauvegardé,
                                                        # dès la première erreur
                                                        "insert"

                                                        # Sauvegarde par do_nothing,
                                                        # ne fait rien en cas d'erreur
                                                        "do_nothing"

                                                        # Sauvegarde par upsert,
                                                        # update ligne à ligne
                                                        "upsert"

                                    # Foreign Keys, pour validation des clés étrangères
                                    "foreign_key": ("attr_01", "attr_01", ....)
                                }
        """
        super().__init__(validators, dict_flow, params_dict)
        self.nb_errors_max = params_dict.get("nb_errors_max")
        self.insert_method = params_dict.get("insert_method")
        self.foreign_key = params_dict.get("foreign_key", tuple())

    def is_valid(self, datas, cursor):
        """
        Validation des données par la méthode is_valid
        :param datas: Données à valider
        :param cursor: cursor de connexion à la BDD Postgresql du Projet
        :return: (Bool errors), "texte pour affichage éventuel"
        """


class PydanticValidation(ValidationTemplate):
    """Validation par les formulaires django"""

    def __init__(
        self,
        validators: [
            [
                BaseModel,
                ModelSchema,
                seria.Serializer,
                seria.ModelSerializer,
                forms.Form,
                forms.ModelForm,
            ],
            FormErrorsTemplate,
        ],
        dict_flow: Dict,
        params_dict: Dict,
    ):
        """
        :param validators:  Tuple formé d'un Form Validateur et de la class Errors du Validateur
        :param dict_flow:   Itérable de dict, pour validation par **kwargs
        :param params_dict: Dictionnaire des paramètres :
                                params_dict = {
                                    # Nom du flux pour le nommage des erreurs du fichier, api, ...
                                    "flow_name": "flow_name",

                                    # Nombre d'erreurs maximum avant arrêt de la validation
                                    "nb_errors_max": 100,

                                    # Methode d'insertion en base des données une fois validées
                                    "insert_method":
                                                        # jeux de données non sauvegardé,
                                                        # dès la première erreur
                                                        "insert"

                                                        # Sauvegarde par do_nothing,
                                                        # ne fait rien en cas d'erreur
                                                        "do_nothing"

                                                        # Sauvegarde par upsert,
                                                        # update ligne à ligne
                                                        "upsert"

                                    # Foreign Keys, pour validation des clés étrangères
                                    "foreign_key": ("attr_01", "attr_01", ....)
                                }
        """
        super().__init__(validators, dict_flow, params_dict)
        self.nb_errors_max = params_dict.get("nb_errors_max")
        self.insert_method = params_dict.get("insert_method")
        self.foreign_key = params_dict.get("foreign_key", tuple())

    def is_valid(self, datas, cursor):
        """
        Validation des données par la méthode is_valid
        :param datas: Données à valider
        :param cursor: cursor de connexion à la BDD Postgresql du Projet
        :return: (Bool errors), "texte pour affichage éventuel"
        """


class Validation:
    """
    Validation des modèles de données à intégrer en base
    """

    def __init__(
        self,
        dict_flow: Iterable[Dict],
        model: models.Model,
        validator: [
            BaseModel,
            ModelSchema,
            seria.Serializer,
            seria.ModelSerializer,
            forms.Form,
            forms.ModelForm,
        ] = None,
        params_dict: Dict = None,
    ):
        """
        :param dict_flow:   Itérable de dict, pour validation par **kwargs
        :param model:       Model au sens Django
        :param validator:   Validateur de données peut être forms, serializer, pydantic, ....
        :param params_dict: Dictionnaire des paramètres :
                                params_dict = {
                                    # Nom du flux pour le nommage des erreurs du fichier, api, ...
                                    "flow_name": "flow_name",

                                    # Nombre d'erreurs maximum avant arrêt de la validation
                                    "nb_errors_max": 100,

                                    # Methode d'insertion en base des données une fois validées
                                    "insert_method":
                                                        # jeux de données non sauvegardé,
                                                        # dès la première erreur
                                                        "insert"

                                                        # Sauvegarde par do_nothing,
                                                        # ne fait rien en cas d'erreur
                                                        "do_nothing"

                                                        # Sauvegarde par upsert,
                                                        # update ligne à ligne
                                                        "upsert"

                                    # Foreign Keys, pour validation des clés étrangères
                                    "foreign_key": ("attr_01", "attr_01", ....)

                                    # tuple des class de ValidationTemplate et FormErrorsTemplate
                                    "validation": (ValidationTemplate, FormErrorsTemplate)
                                }
        """
        self.dict_flow = dict_flow
        self.model = model
        self.params_dict = params_dict or {}
        self._get_params_default()
        self.validator = validator
        self.to_validate = None

    def _get_params_default(self):
        """
        Attribue les valeurs par défaut nécéssaires pour la validation
        :return:
        """
        if "flow_name" not in self.params_dict:
            self.params_dict["flow_name"] = str(uuid.uuid4())

        if "nb_errors_max" not in self.params_dict:
            self.params_dict["nb_errors_max"] = 100

        if "insert_method" not in self.params_dict:
            self.params_dict["insert_method"] = "insert"

    def get_validation_instance(self):
        """Instance le validateur désiré"""

        if isinstance(self.validator, (str,)):
            validation_test = self.params_dict.get("validation")

            if not isinstance(validation_test, (tuple, list)) and len(validation_test) != 2:
                raise ValidationErrors(
                    "l'attribut 'validation' du paramètre params_dict "
                    "doit être un tuple ou une liste : (ValidationTemplate, FormErrorsTemplate)"
                )

            validation, form_errors = self.params_dict.get("validation")

            if not isinstance(validation, (type(ValidationTemplate),)):
                raise ValidationErrors(
                    "La class Validation doit être un instance de ValidationTemplate"
                )

            if not isinstance(form_errors, (type(FormErrorsTemplate),)):
                raise ValidationErrors(
                    "La class Validation doit être un instance de FormErrorsTemplate"
                )

            self.to_validate = validation(
                validators=(self.validator, form_errors),
                dict_flow=self.dict_flow,
                params_dict=self.params_dict,
            )

        elif isinstance(self.validator, (type(forms.Form), type(forms.ModelForm))):
            self.to_validate = DjangoValidation(
                validators=(self.validator, DjangoFormErrors),
                dict_flow=self.dict_flow,
                params_dict=self.params_dict,
            )
        elif isinstance(self.validator, (type(seria.Serializer), type(seria.ModelSerializer))):
            self.to_validate = DrfValidation(
                validators=(self.validator, DrfFormErrors),
                dict_flow=self.dict_flow,
                params_dict=self.params_dict,
            )
        elif isinstance(self.validator, (type(BaseModel), type(ModelSchema))):
            self.to_validate = PydanticValidation(
                validators=(self.validator, PydanticFormErrors),
                dict_flow=self.dict_flow,
                params_dict=self.params_dict,
            )
        else:
            raise ValidationErrors(
                f"Le type de validateur {str(self.validator)}est inconnu "
                "ou l'attribut 'validation' du paramètre params_dict est manquant"
            )

    def validate(self):
        """Lancement de la validation"""
        return self.to_validate.validate()


if __name__ == "__main__":
    CACHE = CacheRegistry()
    CACHE.set("t", "test")
    print(CACHE.get("t"))
    CACHE.set("e", ["error"])
    print(CACHE.get("e"))
    UUID = str(uuid.uuid4())
    CACHE.set(UUID, "errors")
    print(CACHE.get(UUID))
