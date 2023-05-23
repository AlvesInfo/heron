# pylint: disable=C0303,E0401,E1101
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
from itertools import chain
import uuid
from typing import Any, Dict, Iterable

import pendulum
import pydantic
from pydantic import BaseModel, ValidationError
from djantic import ModelSchema
from rest_framework import serializers as seria

from django import forms
from django.db import connection, models
from django.db.models import Count, Q
from django.utils import timezone

# noinspection PyCompatibility
from heron.loggers import LOGGER_VALIDATION
from .exceptions import (
    ValidationError,
    ValidationFormError,
    IsValidError,
    FluxtypeError,
)
from .models import Trace, Line, Error


class TraceTemplate:
    """
    Implémentation de sauvegarde de traces d'import de flux
    """

    def __init__(self, params_dict: Dict):
        """
        :param params_dict: Dictionnaire des paramètres :
                            params_dict = {

                                # Instance de trace au cas où l'on veut suivre de bout en bout
                                "trace": Trace.instance

                                # Numéro de suivi de trace de bout en bout
                                "trace_uuid": "uuid4"

                                # Nom de la trace de bout en bout
                                "trace_name": "trace_name"

                                # Nom du fichier de bout en bout
                                "file_name": "trace_name"

                                # Application ou user ayant envoyé le flux
                                "application_name": "application_name"

                                # Nom du flux pour le nommage des erreurs du fichier, api, ...
                                "flow_name": "flow_name",
        """
        self.trace_number = params_dict.get("trace_uuid") or uuid.uuid4()
        self.params_dict = params_dict
        self.trace = params_dict.get("trace") or self.initialize()
        self.errors = False

    def initialize(self):
        """
        Initialisation de la Trace
        """
        print("AVANT INITIALIZE")
        self.trace = Trace.objects.create(
            created_at=timezone.now(),
            uuid_identification=self.trace_number,
            trace_name=self.params_dict.get("trace_name"),
            file_name=self.params_dict.get("file_name"),
            application_name=self.params_dict.get("application_name"),
            flow_name=self.params_dict.get("flow_name"),
            comment=self.params_dict.get("comment"),
            created_numbers_records=0,
            updated_numbers_records=0,
            errors_numbers_records=0,
            unknown_numbers_records=0,
        )
        print("APRES INITIALIZE", self.trace)
        return self.trace

    def get_formatted_error(self, error_validator):
        """
        Formatage de l'erreur passée en paramètre
        :param error_validator: Erreur arrivée du validateur
        :return: Dict
        """
        raise NotImplementedError

    def add_line(
        self, insertion_type: str = "Unknown", num_line: int = None, designation: str = None
    ):
        """
        Ajoute une ligne à l'instance self.trace_instance
        :param insertion_type:  Type d'insertion dans la table:
                                    "Create"  Pour une ligne en création
                                    "Update"  Pour une ligne en update
                                    "Errors"  Pour une ligne en erreur
                                    "Passed"  Pour une ligne en update
                                    "Unknown" Pour une ligne en inconnue sera mis par défaut
        :param num_line:        N° de ligne traitée
        :param designation:     Désignation de la ligne à inserrer
        """
        insertion_dict = {
            "Create": "cette ligne à bien été créée",
            "Update": "cette ligne à bien été modifiée",
            "Errors": "Cette ligne à généré une erreur",
            "Passed": "Cette ligne n'a pas été traitée",
            "Unknown": "Cette ligne n'a pas été traitée",
        }
        uuid_line_identification = uuid.uuid4()
        line = Line.objects.create(
            **{
                "uuid_identification": uuid_line_identification,
                "trace": self.trace,
                "insertion_type": insertion_type,
                "num_line": num_line,
                "designation": designation or insertion_dict.get(insertion_type),
            }
        )
        return line

    def add_error(self, num_line: str, error: Any):
        """
        Ajout d'une ligne d'erreur dans la trace
        :param num_line: N° de ligne traitée
        :param error:    Erreurs venant de la validation. Les erreurs par lignes seront traduitent
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
        self.errors = True
        formatted_errors = self.get_formatted_error(error)
        line = self.add_line(insertion_type="Errors", num_line=num_line)

        for attr_name, errors_list in formatted_errors.items():

            Error.objects.bulk_create(
                [
                    Error(
                        **{
                            "line": line,
                            "attr_name": attr_name,
                            "message": messages_dict.get("message"),
                            "data_expected": messages_dict.get("data_expected"),
                            "data_received": messages_dict.get("data_received"),
                        }
                    )
                    for messages_dict in errors_list
                ]
            )

    def save(self):
        """Sauvegarde de l'ensemble de la trace y compris les lignes et les erreurs"""

        # Sauvegarde finale, pour le comptage des differents état des enregistrements
        create = Count("insertion_type", filter=Q(insertion_type="Create"))
        update = Count("insertion_type", filter=Q(insertion_type="Update"))
        errors = Count("insertion_type", filter=Q(insertion_type="Errors"))
        passed = Count("insertion_type", filter=Q(insertion_type="Passed"))
        unknown = Count("insertion_type", filter=Q(insertion_type="Unknown"))
        counts_dict = Line.objects.filter(trace=self.trace.uuid_identification).aggregate(
            create=create, update=update, errors=errors, passed=passed, unknown=unknown
        )

        self.trace.final_at = timezone.now()
        self.trace.errors = self.errors
        self.trace.created_numbers_records = counts_dict.get("create")
        self.trace.updated_numbers_records = counts_dict.get("update")
        self.trace.errors_numbers_records = counts_dict.get("errors")
        self.trace.passed_numbers_records = counts_dict.get("passed")
        self.trace.unknown_numbers_records = counts_dict.get("unknown")
        self.trace.save()

        # mise à jour des champs de colonnes pour avoir une meilleure indication dans les traces
        with connection.cursor() as cursor:
            cursor.execute(
                """
            update data_flux_error err 
            set file_column = maj.file_column
            from (
                select dfe.id, ec.file_column
                from data_flux_trace dft  
                join data_flux_line dfl 
                on dft.uuid_identification = dfl.trace 
                join data_flux_error dfe 
                on dfl.uuid_identification = dfe.line 
                join edi_columndefinition ec  
                on dft.flow_name = ec.flow_name 
                and dfe.attr_name = ec.attr_name 
                where dft.uuid_identification = %(uuid_identification)s
                and dfe.file_column isnull
            ) maj
            where err.id = maj.id
            """,
                {"uuid_identification": self.trace.uuid_identification},
            )


class DjangoTrace(TraceTemplate):
    """
    Formate la sortie des erreurs de validation pour les formulaires Django
    """

    def get_formatted_error(self, error_validator):
        """
        Formatage de l'erreur passée en paramètre
        :param error_validator: Erreur arrivée du validateur
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
        :param error_validator: Erreur arrivée du validateur
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
            LOGGER_VALIDATION.exception("Erreur sur DrfTrace.get_formatted_error")
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
        :param error_validator: Erreur arrivée du validateur,
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

                                                        # Sauvegarde avec prévalidation
                                                        # des clés étangères et
                                                        # contraintes d'unicité
                                                        "pre_validation"

                                    # Si "insert_method" == "pre_validation"
                                    "trace": trace suivie de bout en bout

                                    # Fichier de type io.StringIO, pour écrire les données cleannées
                                    "file_io": file_io
                                }
        """
        # TODO : Finir d'implémenter la sauvegarde des clés étangères et contraintes d'unicité
        self.validator_class, self.trace_class = validators
        self.trace_instance = self.trace_class(params_dict)
        self.dict_flow = dict_flow
        self.first_element = next(iter(dict_flow))
        self.trace = 0
        self.params_dict = params_dict

    def _add_line(
        self, insertion_type: str = "Unknown", num_line: int = None, designation: str = None
    ):
        """
        Ajoute une ligne à l'instance self.trace_instance
        :param insertion_type:  Type d'insertion dans la table:
                                    "Create"  Pour une ligne en création
                                    "Update"  Pour une ligne en update
                                    "Errors"  Pour une ligne en erreur
                                    "Passed"  Pour une ligne en update
                                    "Unknown" Pour une ligne en inconnue sera mis par défaut
        :param num_line:        N° de ligne traitée
        :param designation:     Désignation de la ligne à inserrer
        """
        self.trace_instance.add_line(insertion_type, num_line, designation)

    def _add_error(self, line, error):
        """
        Ajoute une erreur à l'instance self.trace_instance
        :param line: N° de ligne traitée
        :param error: erreur sur la ligne concernée
        """
        self.trace_instance.add_error(line, error)

    def _save_errors_trace(self):
        """
        Sauvergarde toutes les erreurs de l'instance self.trace_instance
        """
        self.trace_instance.save()

    def is_valid(self, validator, data_dict, csv_writer):
        """
        Validation des données par la méthode is_valid
        :param validator:  Validateur
        :param data_dict:  Dictionnaire des données à valider
        :param csv_writer: csv_writer pour écrire les données cleannées, dans un fichier io.StringIO
        :return: None ou errors
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

        lines = set()
        nb_errors = 0
        nb_errors_max = self.params_dict.get("nb_errors_max", 0)
        file_io = self.params_dict.get("file_io")
        csv_writer = csv.writer(
            file_io,
            delimiter=";",
            quotechar='"',
            lineterminator="\n",
            quoting=csv.QUOTE_ALL,
            escapechar='"',
        )
        try:

            for num_line, data_dict in enumerate(chain([self.first_element], self.dict_flow), 1):
                error_message = self.is_valid(self.validator_class, data_dict, csv_writer)

                if error_message:
                    lines.add(num_line)
                    self._add_error(line=num_line, error=error_message)
                    nb_errors += 1

                # si l'on dépasse le nombre d'erreurs max demandées,
                # alors on stoppe le contrôle des lignes
                if nb_errors_max and nb_errors >= nb_errors_max:
                    break

        except Exception as except_error:
            now = pendulum.now().format(r"\du dddd DD MMMM YYYY à HH:MM:SS", locale="fr")
            self._add_error(
                line=0,
                error=(
                    "Une erreur c'est produite à l'appel de validate, "
                    f"vérifier les fichiers de log {now}"
                ),
            )
            LOGGER_VALIDATION.exception("Erreur sur ValidationTemplate.validate")
            raise ValidationFormError(
                "Une erreur c'est produite à l'appel de validate"
            ) from except_error

        finally:
            self.trace_instance.save()

        return lines


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
                                params_dict = {}
        """
        super().__init__(validators, dict_flow, params_dict)

    def is_valid(self, validator, data_dict, csv_writer):
        """
        Validation des données par la méthode is_valid
        :param validator:  Validateur
        :param data_dict:  Dictionnaire des données à valider
        :param csv_writer: csv_writer pour écrire les données cleannées, dans un fichier io.StringIO
        :return: None ou errors
        """
        form = validator(**data_dict)

        if form.is_valid():
            csv_writer.writerow([form.cleaned_data.get(key) for key in validator.Config.include])
            return False

        return form.errors


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
                                params_dict = {}
        """
        super().__init__(validators, dict_flow, params_dict)

    def is_valid(self, validator, data_dict, csv_writer):
        """
        Validation des données par la méthode is_valid
        :param validator:  Validateur
        :param data_dict:  Dictionnaire des données à valider
        :param csv_writer: csv_writer pour écrire les données cleannées, dans un fichier io.StringIO
        :return: None ou errors
        """
        form = validator(**data_dict)

        if form.is_valid():
            csv_writer.writerow([form.data.get(key) for key in validator.Config.include])
            return False

        return form.errors


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
                                params_dict = {}
        """
        super().__init__(validators, dict_flow, params_dict)

    def is_valid(self, validator, data_dict, csv_writer):
        """
        Validation des données par la méthode is_valid
        :param validator:  Validateur
        :param data_dict:  Dictionnaire des données à valider
        :param csv_writer: csv_writer pour écrire les données cleannées, dans un fichier io.StringIO
        :return: None ou errors
        """
        try:
            form = validator(**data_dict)
            csv_writer.writerow([form.dict().get(key) for key in validator.Config.include])

        except (pydantic.error_wrappers.ValidationError, ValidationError) as except_error:
            return except_error.errors(), data_dict

        return False


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
        :param dict_flow:   Itérable de dict, pour validation
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

                                    # Fichier de type io.StringIO, pour écrire les données cleannées
                                    "file_io": file_io
                                }
        """
        self.dict_flow = dict_flow
        self.model = model
        self.params_dict = params_dict or {}
        self.get_params_default()
        self.validator = validator
        self.to_validate = None
        self.get_validation_instance()

    def get_params_default(self):
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
        """Instancie le validateur désiré"""

        if self.validator is None:
            validation_test = self.params_dict.get("validation")

            if not isinstance(validation_test, (tuple, list)) and len(validation_test) != 2:
                raise ValidationFormError(
                    "l'attribut 'validation' du paramètre params_dict "
                    "doit être un tuple ou une liste : (ValidationTemplate, TraceTemplate)"
                )

            validation, trace = self.params_dict.get("validation")

            if not isinstance(validation, (type(ValidationTemplate),)):
                raise ValidationFormError(
                    "La class Validation doit être un instance de ValidationTemplate"
                )

            if not isinstance(trace, (type(TraceTemplate),)):
                raise ValidationFormError("La class Trace doit être un instance de TraceTemplate")

        elif isinstance(self.validator, (type(forms.Form), type(forms.ModelForm))):
            validation = DjangoValidation
            trace = DjangoTrace

        elif isinstance(self.validator, (type(seria.Serializer), type(seria.ModelSerializer))):
            validation = DrfValidation
            trace = DrfTrace

        elif isinstance(self.validator, (type(BaseModel), type(ModelSchema))):
            validation = PydanticValidation
            trace = PydanticTrace

        else:
            raise ValidationFormError(
                f"Le type de validateur {str(self.validator)}est inconnu "
                "ou l'attribut 'validation' du paramètre params_dict est manquant"
            )

        self.to_validate = validation(
            validators=(self.validator, trace),
            dict_flow=self.dict_flow,
            params_dict=self.params_dict,
        )

    def validate(self):
        """Lancement de la validation"""
        self.params_dict.get("file_io").seek(0)
        self.params_dict.get("file_io").seek(0)
        error_lines = self.to_validate.validate()
        return error_lines
