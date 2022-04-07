# pylint: disable=E0401,
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
import csv
import io
from itertools import chain
import uuid
from typing import Any, Dict, Iterable

import pendulum
from pydantic import BaseModel
from djantic import ModelSchema
from rest_framework import serializers as seria

from django.db import models
from django.db.models import Count, Q
from django import forms

# noinspection PyCompatibility
from exceptions import ValidationError, IsValidError, FluxtypeError
from models import Trace, Line, Error
from .loggers import VALIDATION_LOGGER


class TraceTemplate:
    """
    Implémentation de sauvegarde de traces d'import de flux
    """

    def __init__(self, params_dict: Dict):
        """
        :param params_dict: Dictionnaire des paramètres :
                        params_dict = {

                            # Numéro de suivi de trace de bout en bout
                            "trace_tracking_number": "uuid4"

                            # Nom de la trace de bout en bout
                            "trace_tracking_name": "trace_name"

                            # Application ou user ayant envoyé le flux
                            "application_name": "application_name"

                            # Nom du flux pour le nommage des erreurs du fichier, api, ...
                            "flow_name": "flow_name",
        """
        self.trace_number = params_dict.get("trace_tracking_number") or uuid.uuid4()
        self.trace = self.initialize(
            params_dict.get("trace_tracking_name"),
            params_dict.get("application_name"),
            params_dict.get("flow_name"),
            params_dict.get("comment"),
        )
        self.lines_list = []
        self.errors_list = []

    def initialize(self, trace_name, application_name, flow_name, comment):
        """
        Instanciation du models Trace, Attributes :
                                                    uuid_identification
                                                    trace_name
                                                    application_name
                                                    flow_name
                                                    errors
                                                    comment
                                                    created_numbers_records
                                                    updated_numbers_records
                                                    errors_numbers_records
        param trace_tracking_number: N° de Trace de bout en bout
        """
        self.trace = Trace.objects.create(
            uuid_identification=self.trace_number,
            trace_name=trace_name,
            application_name=application_name,
            flow_name=flow_name,
            comment=comment,
            created_numbers_records=0,
            updated_numbers_records=0,
            errors_numbers_records=0,
            unknown_numbers_records=0,
        )
        return self.trace

    def get_formatted_error(self, error_validator):
        """
        Formatage de l'erreur passée en paramètre
        :param error_validator: erreur arrivée du validateur
        :return: Dict
        """
        raise NotImplementedError

    def add_line(
        self, insertion_type: str = "Unknown", num_line: int = None, designation: str = None
    ):
        """
        Ajoute une ligne à l'instance self.trace_instance
        :param insertion_type:  type d'insertion dans la table:
                                    "Create"  Pour une ligne en création
                                    "Update"  Pour une ligne en update
                                    "Errors"  Pour une ligne en erreur
                                    "Passed"  Pour une ligne en update
                                    "Unknown" Pour une ligne en inconnue sera mis par défaut
        :param num_line: N° de ligne traitée
        :param designation: désignation de la ligne à inserrer
        """
        insertion_dict = {
            "Create": "cette ligne à bien été créée",
            "Update": "cette ligne à bien été modifiée",
            "Errors": "Cette ligne à généré une erreur",
            "Passed": "Cette ligne n'a pas été traitée",
            "Unknown": "Cette ligne n'a pas été traitée",
        }
        uuid_line_identification = uuid.uuid4()
        self.lines_list.append(
            {
                "uuid_identification": uuid_line_identification,
                "trace": self.trace.uuid_identification,
                "insertion_type": insertion_type,
                "num_line": num_line,
                "designation": designation or insertion_dict.get(insertion_type),
            }
        )
        return uuid_line_identification

    def add_error(self, num_line: str, error: Any):
        """
        Ajout d'une ligne d'erreur dans la trace
        :param num_line:    N° de ligne traitée
        :param error:   Erreurs venant de la validation. Les erreurs par lignes seront traduitent
                        par la trace du validator qui sera organisé comme suit:
                        error_dict = {
                            "champ_00": [
                                {
                                    "message": "message_01",
                                    "data_expected": "donnée_01 attendue",
                                    "data_received": "donnée_01 reçue",
                                },
                                {
                                    "message": "message_02",
                                    "data_expected": "donnée_02 attendue",
                                    "data_received": "donnée_02 reçue",
                                }, ...
                            ],
                            "champ_02": [
                                {
                                    "message": "message_01",
                                    "data_expected": "donnée_01 attendue",
                                    "data_received": "donnée_01 reçue",
                                },
                            ], ...
                        }
        """
        errors_format = self.get_formatted_error(error)

        for attribute, errors_list in errors_format.items():
            uuid_error_line = self.add_line(insertion_type="Errors", num_line=num_line)

            for messages_dict in errors_list:
                self.errors_list.append(
                    {
                        "line": uuid_error_line,
                        "attribute": attribute,
                        "message": messages_dict.get("message"),
                        "data_expected": messages_dict.get("data_expected"),
                        "data_received": messages_dict.get("data_received"),
                    }
                )

    def save(self):

        """Sauvegarde finale, pour le comptage des differents état des enregistrements"""
        create = Count("insertion_type", filter=Q(insertion_type="Create"))
        update = Count("insertion_type", filter=Q(insertion_type="Update"))
        errors = Count("insertion_type", filter=Q(insertion_type="Errors"))
        passed = Count("insertion_type", filter=Q(insertion_type="Passed"))
        unknown = Count("insertion_type", filter=Q(insertion_type="Unknown"))
        counts_dict = Line.objects.filter(trace="316519e0-fb3a-414c-ad68-15585b4f6bf4").aggregate(
            create=create, update=update, errors=errors, passed=passed, unknown=unknown
        )
        self.trace.update(
            created_numbers_records=counts_dict.get("create"),
            updated_numbers_records=counts_dict.get("update"),
            errors_numbers_records=counts_dict.get("errors"),
            passed_numbers_records=counts_dict.get("passed"),
            unknown_numbers_records=counts_dict.get("unknown"),
        )


class DjangoTrace(TraceTemplate):
    """
    Formate la sortie des erreurs de validation pour les formulaires Django
    """

    def get_formatted_error(self, error_validator):
        """
        Formatage de l'erreur passée en paramètre
        :param error_validator: erreur arrivée du validateur
        :return: {
                    "champ_00": [
                                    {
                                        "message": "message_01",
                                        "data_expected": "donnée_01 attendue",
                                        "data_received": "donnée_01 reçue",
                                    },
                                    {
                                        "message": "message_02",
                                        "data_expected": "donnée_02 attendue",
                                        "data_received": "donnée_02 reçue",
                                    }, ...
                    ],
                    "champ_02": [
                                    {
                                        "message": "message_01",
                                        "data_expected": "donnée_01 attendue",
                                        "data_received": "donnée_01 reçue",
                                    },
                    ], ...
                }
        """
        error_dict = {
            key: [
                {
                    "message": str(value),
                    "data_received": "aucune valeur reçue"
                    if not error_validator.data.get(key)
                    else error_validator.data.get(key),
                }
                for value in row
            ]
            for key, row in error_validator.errors.items()
        }
        return error_dict


class DrfTrace(TraceTemplate):
    """
    Formate la sortie des erreurs de validation pour les serializers DRF
    """

    def get_formatted_error(self, error_validator):
        """
        Formatage de l'erreur passée en paramètre
        :param error_validator: erreur arrivée du validateur
        :return: {
                    "champ_00": [
                                    {
                                        "message": "message_01",
                                        "data_expected": "donnée_01 attendue"
                                        "data_received": "donnée_01 reçue"
                                    },
                                    {
                                        "message": "message_02",
                                        "data_expected": "donnée_02 attendue"
                                        "data_received": "donnée_02 reçue"
                                    }, ...
                    ],
                    "champ_02": [
                                    {
                                        "message": "message_01",
                                        "data_expected": "donnée_01 attendue"
                                        "data_received": "donnée_01 reçue"
                                    },
                    ], ...
                }
        """
        try:
            error_dict = {
                key: [
                    {
                        "message": str(value),
                        "data_received": "aucune valeur reçue"
                        if not error_validator.data.get(key)
                        else error_validator.data.get(key),
                    }
                    for value in row
                ]
                for key, row in error_validator.errors.items()
            }
            return error_dict
        except AssertionError as except_error:
            VALIDATION_LOGGER.exception("Erreur sur DrfTrace.get_formatted_error")
            raise IsValidError(
                "validator.errors a été appelé avant validator.is_valid()"
            ) from except_error


class PydanticTrace(TraceTemplate):
    """
    Formate la sortie des erreurs de validation pour les models Pydantic
    """

    def get_formatted_error(self, error_validator):
        """
        Formatage de l'erreur passée en paramètre
        :param error_validator: erreur arrivée du validateur,
                                sous forme de tuple (erreurs, data_received)
        :return: {
                    "champ_00": [
                                    {
                                        "message": "message_01",
                                        "data_expected": "donnée_01 attendue"
                                        "data_received": "donnée_01 reçue"
                                    },
                                    {
                                        "message": "message_02",
                                        "data_expected": "donnée_02 attendue"
                                        "data_received": "donnée_02 reçue"
                                    }, ...
                    ],
                    "champ_02": [
                                    {
                                        "message": "message_01",
                                        "data_expected": "donnée_01 attendue"
                                        "data_received": "donnée_01 reçue"
                                    },
                    ], ...
                }
        """
        errors_dict, data_dict = error_validator
        error_dict = {
            ", ".join(dict_row.get("loc")): [
                {
                    "message": dict_row.get("msg"),
                    "data_received": "aucune valeur reçue"
                    if not data_dict.get(", ".join(dict_row.get("loc")))
                    else data_dict.get(", ".join(dict_row.get("loc"))),
                }
            ]
            for dict_row in errors_dict
        }
        return error_dict


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
            TraceTemplate,
        ],
        dict_flow: Iterable[Dict],
        params_dict: Dict,
    ):
        """
        :param validators:  Tuple formé d'un Form Validateur et de la class Errors du Validateur
        :param dict_flow:   Itérable de dict, pour validation par **kwargs
        :param params_dict: Dictionnaire des paramètres :
                                params_dict = {

                                    # Numéro de suivi de trace de bout en bout
                                    "trace_tracking_number": "uuid4"

                                    # Nom de la trace de bout en bout
                                    "trace_tracking_name": "trace_name"

                                    # Application ou user ayant envoyé le flux
                                    "application_name": "application_name"

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

                                    # Foreign Keys, pour validation des clés étrangères,
                                    # non implémenté pour le moment
                                    "foreign_key": ("attr_01", "attr_01", ....)
                                }
        """
        self.validator_class, self.errors_class = validators
        self.trace_instance = self.errors_class(params_dict)
        self.dict_flow = dict_flow
        self.first_element = next(iter(dict_flow))
        self.nb_errors_max = params_dict.get("nb_errors_max")

    def _add_error(self, line, error):
        """
        Ajoute une erreur à l'instance self.trace_instance
        :param line: N° de ligne traitée
        :param error: erreur sur la ligne concernée
        """
        self.trace_instance.add_error(line, error)

    def _save_errors_trace(self, cursor):
        """
        Sauvergarde toutes les erreurs de l'instance self.trace_instance
        :param cursor: cursor de connexion à la BDD Postgresql du Projet
        """
        self.trace_instance.save(cursor)

    def is_valid(self, data_dict, cursor):
        """
        Validation des données par la méthode is_valid
        :param data_dict: Données à valider
        :param cursor: cursor de connexion à la BDD Postgresql du Projet
        :return: (Bool errors), "texte pour affichage éventuel"
        """
        raise NotImplementedError

    def validate(self):
        """Lancement de la validation"""
        if not isinstance(self.first_element, (dict,)):
            now = pendulum.now().format(r"\du dddd DD MMMM YYYY à HH:MM:SS", locale="fr")
            self._add_error(
                line=0, error=f"La validation n'a pu avoir lieu, vérifier les fichiers de log {now}"
            )
            raise FluxtypeError(
                "La validation ne peut avoir lieu car le flux des données, "
                "doit être un flux de dictionnaires"
            )

        try:

            for data_dict in enumerate(chain([self.first_element], self.dict_flow), 1):
                pass

        except Exception as except_error:
            now = pendulum.now().format(r"\du dddd DD MMMM YYYY à HH:MM:SS", locale="fr")
            self._add_error(
                line=0,
                error=(
                    "Une erreur c'est produite à l'appel de validate, "
                    f"vérifier les fichiers de log {now}"
                ),
            )
            VALIDATION_LOGGER.exception("Erreur sur ValidationTemplate.validate")
            raise ValidationError(
                "Une erreur c'est produite à l'appel de validate"
            ) from except_error


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
            TraceTemplate,
        ],
        dict_flow: Dict,
        params_dict: Dict,
    ):
        """
        :param validators:  Tuple formé d'un Form Validateur et de la class Errors du Validateur
        :param dict_flow:   Itérable de dict, pour validation par **kwargs
        :param params_dict: Dictionnaire des paramètres :
                                params_dict = {

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

                                    # Foreign Keys, pour validation des clés étrangères,
                                    # non implémenté pour le moment
                                    "foreign_key": ("attr_01", "attr_01", ....)
                                }
        """
        super().__init__(validators, dict_flow, params_dict)
        self.insert_method = params_dict.get("insert_method")
        self.foreign_key = params_dict.get("foreign_key", tuple())

    def is_valid(self, data_dict, cursor):
        """
        Validation des données par la méthode is_valid
        :param data_dict: Données à valider
        :param cursor: cursor de connexion à la BDD Postgresql du Projet
        :return: (Bool errors), "texte pour affichage éventuel"
        """


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
            TraceTemplate,
        ],
        dict_flow: Dict,
        params_dict: Dict,
    ):
        """
        :param validators:  Tuple formé d'un Form Validateur et de la class Errors du Validateur
        :param dict_flow:   Itérable de dict, pour validation par **kwargs
        :param params_dict: Dictionnaire des paramètres :
                                params_dict = {

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

                                    # Foreign Keys, pour validation des clés étrangères,
                                    # non implémenté pour le moment,
                                    # non implémenté pour le moment
                                    "foreign_key": ("attr_01", "attr_01", ....)
                                }
        """
        super().__init__(validators, dict_flow, params_dict)
        self.nb_errors_max = params_dict.get("nb_errors_max")
        self.insert_method = params_dict.get("insert_method")
        self.foreign_key = params_dict.get("foreign_key", tuple())

    def is_valid(self, data_dict, cursor):
        """
        Validation des données par la méthode is_valid
        :param data_dict: Données à valider
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
            TraceTemplate,
        ],
        dict_flow: Dict,
        params_dict: Dict,
    ):
        """
        :param validators:  Tuple formé d'un Form Validateur et de la class Errors du Validateur
        :param dict_flow:   Itérable de dict, pour validation par **kwargs
        :param params_dict: Dictionnaire des paramètres :
                                params_dict = {

                                    # Nombre d'erreurs maximum avant arrêt de la validation
                                    "nb_errors_max": 100,

                                    # Methode d'insertion en base des données une fois validées
                                    "insert_method": "insert" ou "do_nothing" ou "upsert"

                                    # Foreign Keys, pour validation des clés étrangères,
                                    # non implémenté pour le moment
                                    "foreign_key": ("attr_01", "attr_01", ....)
                                }
        """
        super().__init__(validators, dict_flow, params_dict)
        self.nb_errors_max = params_dict.get("nb_errors_max")
        self.insert_method = params_dict.get("insert_method")
        self.foreign_key = params_dict.get("foreign_key", tuple())

    def is_valid(self, data_dict, cursor):
        """
        Validation des données par la méthode is_valid
        :param data_dict: Données à valider
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

                                    # Numéro de suivi de trace de bout en bout
                                    "trace_tracking_number": "uuid4"

                                    # Nom de la trace de bout en bout
                                    "trace_tracking_name": "trace_name"

                                    # Application ou user ayant envoyé le flux
                                    "application_name": "application_name"

                                    # Nom du flux pour le nommage des erreurs du fichier, api, ...
                                    "flow_name": "flow_name",

                                    # Nombre d'erreurs maximum avant arrêt de la validation
                                    "nb_errors_max": 100,

                                    # Methode d'insertion en base des données une fois validées
                                    "insert_method": "insert" ou "do_nothing" ou "upsert"

                                    # Foreign Keys, pour validation des clés étrangères,
                                    # non implémenté pour le moment
                                    "foreign_key": ("attr_01", "attr_01", ....)

                                    # tuple des class de ValidationTemplate et TraceTemplate
                                    "validation": (ValidationTemplate, TraceTemplate)
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
        Attribue les valeurs par défaut nécéssaires pour la validation,
        à l'attribut d'instance self.params_dict
        """
        if "application_name" not in self.params_dict:
            self.params_dict["application_name"] = "unkown"

        if "flow_name" not in self.params_dict:
            self.params_dict["flow_name"] = "unkown"

        if "nb_errors_max" not in self.params_dict:
            self.params_dict["nb_errors_max"] = 100

        if "insert_method" not in self.params_dict:
            self.params_dict["insert_method"] = "insert"

    def get_validation_instance(self):
        """Instance le validateur désiré"""

        if self.validator is None:
            validation_test = self.params_dict.get("validation")

            if not isinstance(validation_test, (tuple, list)) and len(validation_test) != 2:
                raise ValidationError(
                    "l'attribut 'validation' du paramètre params_dict "
                    "doit être un tuple ou une liste : (ValidationTemplate, TraceTemplate)"
                )

            validation, form_errors = self.params_dict.get("validation")

            if not isinstance(validation, (type(ValidationTemplate),)):
                raise ValidationError(
                    "La class Validation doit être un instance de ValidationTemplate"
                )

            if not isinstance(form_errors, (type(TraceTemplate),)):
                raise ValidationError("La class Validation doit être un instance de TraceTemplate")

        elif isinstance(self.validator, (type(forms.Form), type(forms.ModelForm))):
            validation = DjangoValidation
            form_errors = DjangoTrace

        elif isinstance(self.validator, (type(seria.Serializer), type(seria.ModelSerializer))):
            validation = DrfValidation
            form_errors = DrfTrace

        elif isinstance(self.validator, (type(BaseModel), type(ModelSchema))):
            validation = PydanticValidation
            form_errors = PydanticTrace

        else:
            raise ValidationError(
                f"Le type de validateur {str(self.validator)}est inconnu "
                "ou l'attribut 'validation' du paramètre params_dict est manquant"
            )

        # noinspection PyArgumentList
        self.to_validate = validation(
            model=self.model,
            validators=(self.validator, form_errors),
            dict_flow=self.dict_flow,
            params_dict=self.params_dict,
        )

    def validate(self):
        """Lancement de la validation"""
        return self.to_validate.validate()


if __name__ == "__main__":
    from cache import CacheRegistry

    CACHE = CacheRegistry()
    CACHE.set("t", "test")
    print(CACHE.get("t"))
    CACHE.set("e", ["error"])
    print(CACHE.get("e"))
    UUID = str(uuid.uuid4())
    CACHE.set(UUID, "errors")
    print(CACHE.get(UUID))
