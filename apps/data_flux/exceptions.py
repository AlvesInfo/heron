# pylint: disable=
"""Module des Exception du module data_flux

Commentaire:

created at: 2021-10-30
created by: Paulo ALVES

modified at: 2021-10-30
modified by: Paulo ALVES
"""


# Exceptions pour les Imports de fihiers ===========================================================

class DuplicatesError(Exception):
    """Gestion de doublons dans les fichiers"""


class ModelFieldError(Exception):
    """Gestion des valeurs inéxistantes en bdd"""


# Exceptions du module loader ======================================================================

class IterFileToInsertError(Exception):
    """Gestion d'erreur d'itération d'un fichier à insérer"""


class GetAddDictError(IterFileToInsertError):
    """Gestion d'erreur d'itération d'un fichier à insérer"""


class EncodingError(Exception):
    """Exception sniff encodig"""


class ExcelToCsvError(Exception):
    """Exception transformation excel"""


class FileToCsvError(Exception):
    """Exception transformation fichier en csv"""


class ExcelToCsvFileError(Exception):
    """Exception transformation excel"""


class CsvFileToStringIoError(Exception):
    """Exception envoi du fichier dans un StringIO"""


# Exceptions du module validation ==================================================================

class ValidationError(Exception):
    """Gestion d'erreur de validation"""


class ValidationFormError(Exception):
    """Exception du module de Validation"""


class IsValidError(ValidationFormError, AssertionError):
    """Exception sur appel de forms.errors avant fomrs.is_valid()"""


class FluxtypeError(ValidationFormError):
    """Le lux de validation doit être un dictionnaire"""


# Exceptions du module postgres_save ===============================================================

class PostgresDjangoError(Exception):
    """Exceptions pour l'upsert dans une table postgresql"""


class PostgresInsertMethodError(PostgresDjangoError):
    """Exceptions pour l'upsert dans une table postgresql"""


class PostgresCardinalityViolationError(PostgresDjangoError):
    """Exceptions pour l'upsert dans une table postgresql"""


class PostgresUniqueError(PostgresDjangoError):
    """Exceptions pour l'upsert dans une table postgresql"""


class PostgresKeyError(PostgresDjangoError):
    """Exceptions pour une clef demandée qui n'existe pas dans une table postgresql"""


class PostgresTypeError(PostgresDjangoError):
    """Exceptions pour un type en erreur dans une table postgresql"""


class PostgresPreparedError(PostgresDjangoError):
    """Exceptions pour un execute_bach psycopg2"""


# Exceptions des types Path  =======================================================================


class PathTypeError(Exception):
    """
    class of exceptions variables that are not instances of pathlib.Path
    """


class PathFileError(Exception):
    """
    class of exceptions variables that are not instances of pathlib.Path
    """


class PathUnzipError(Exception):
    """
    class of exceptions for unzip errors
    """


# Exceptions du module Opto33 parser ===============================================================


class OptoMontError(ValueError):
    """
    Class for exceptions Opto 33 mont
    """


class OptoDateError(ValueError):
    """
    Class for exceptions Opto 33 date
    """


class OptoLinesError(ValueError):
    """
    Class for exceptions Opto 33 numbers lines
    """


class OptoQualifierError(ValueError):
    """
    Class for exceptions Opto 33 date
    """


class OptoIdError(Exception):
    """Class for exceptions Opto 33 file parser"""


class OptoNumberError(Exception):
    """Class for exceptions Opto 33 file parser"""


class OptoParserError(Exception):
    """Class for exceptions Opto 33 file parser"""
