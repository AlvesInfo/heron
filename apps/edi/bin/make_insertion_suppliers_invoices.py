"""FR : Module d'import des factures founisseurs EDI.

EN : Import module for EDI incoives suppliers.

Commentaire:

created at: 2022-04-08
created by: Paulo ALVES

modified at: 2023-01-01
modified by: Paulo ALVES
"""

import io
from functools import lru_cache
from pathlib import Path
from typing import Any, NoReturn

import redis
from django.db.utils import IntegrityError
from django.utils import timezone
from psycopg2 import sql

from apps.core.functions.functions_setups import connection, settings
from apps.data_flux.exceptions import (
    OptoDateError,
    OptoIdError,
    OptoLinesError,
    OptoNumberError,
    OptoParserError,
    OptoQualifierError,
    PathFileError,
    PathTypeError,
    ValidationError,
)
from apps.data_flux.loader import (
    ExcelToCsvError,
    FileLoader,
    FileToCsvError,
    GetAddDictError,
    IterFileToInsertError,
    Opto33Loader,
)
from apps.data_flux.postgres_save import PostgresDjangoUpsert, PostgresKeyError, PostgresTypeError
from apps.data_flux.validation import PydanticTrace, PydanticValidation, Validation
from apps.edi.models import ColumnDefinition, SupplierDefinition
from apps.edi.parameters.invoices_imports import get_columns, get_first_line, get_loader_params_dict
from heron.loggers import LOGGER_EDI

# Cache redis, remplacé par un dictionnaire local si le serveur est injoignable
# (annotation en chaîne : les tests remplacent redis.StrictRedis à l'import du module)
cache: redis.StrictRedis | dict[str, Any]

try:
    cache = redis.StrictRedis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
    )
except redis.exceptions.ConnectionError:
    cache = {}

proccessing_dir = Path(settings.PROCESSING_SUPPLIERS_DIR)


@lru_cache(maxsize=256)
def get_suppliers(flow_name: str):
    """:param flow_name: Champ flow_name dans la table SupplierDefinition

    :return: Retourne le supplier et l'indentifier du fournisseur dans la table SupplierDefinition
    """
    with connection.cursor() as cursor:
        sql_supplier = sql.SQL(
            """
        select
            "supplier", "supplier_ident"
        from edi_supplierdefinition es
        where "flow_name" = %(flow_name)s
        """
        )
        cursor.execute(sql_supplier, {"flow_name": flow_name})
        results = cursor.fetchall()

    return (results[0][0], results[0][1]) if results else ("", "")


@lru_cache(maxsize=256)
def get_supplier_name(flow_name: str):
    """:param flow_name: Champ flow_name dans la table SupplierDefinition

    :return: Retourne le supplier du fournisseur dans la table SupplierDefinition
    """
    supplier, supplier_ident = get_suppliers(flow_name)

    if isinstance(cache, (dict,)):
        cache[f"{flow_name}_supplier"] = supplier
        cache[f"{flow_name}_ident"] = supplier_ident
    else:
        cache.set(f"{flow_name}_supplier", supplier)
        cache.set(f"{flow_name}_ident", supplier_ident)

    return supplier


@lru_cache(maxsize=256)
def get_supplier_ident(flow_name: str):
    """:param flow_name: Champ flow_name dans la table SupplierDefinition

    :return: Retourne le supplier_ident du fournisseur dans la table SupplierDefinition
    """
    supplier, supplier_ident = get_suppliers(flow_name)

    if isinstance(cache, (dict,)):
        cache[f"{flow_name}_ident"] = supplier_ident
        cache[f"{flow_name}_supplier"] = supplier
    else:
        cache.set(f"{flow_name}_ident", supplier_ident)
        cache.set(f"{flow_name}_supplier", supplier)

    return supplier_ident


def get_cached(key: str):
    """Valeur du cache (redis renvoie des bytes, le dict de repli renvoie des str).

    Un redis injoignable n'empêche pas l'import : on retombe sur la base.
    """
    try:
        value = cache.get(key)
    except redis.exceptions.RedisError:
        return None

    if isinstance(value, bytes):
        value = value.decode()

    return value or None


@lru_cache(maxsize=256)
def get_supplier(flow_name):
    """Get supplier name in cache ou model SupplierDefinition."""
    return get_cached(f"{flow_name}_supplier") or get_supplier_name(flow_name)


@lru_cache(maxsize=256)
def get_ident(flow_name):
    """Get supplier ident in cache ou model SupplierDefinition."""
    return get_cached(f"{flow_name}_ident") or get_supplier_ident(flow_name)


# Exceptions attendues de la chaîne d'import, dans l'ordre où elles sont reconnues, avec le
# libellé journalisé ; toute autre exception est journalisée en "Exception Générale"
LOGGED_EXCEPTIONS = (
    # Exceptions FileLoader
    (GetAddDictError, "GetAddDictError"),
    (IterFileToInsertError, "IterFileToInsertError"),
    (ExcelToCsvError, "ExcelToCsvError"),
    (FileToCsvError, "FileToCsvError"),
    # Exceptions Opto33Loader
    (OptoDateError, "OptoDateError"),
    (OptoLinesError, "OptoLinesError"),
    (OptoQualifierError, "OptoQualifierError"),
    (OptoIdError, "OptoIdError"),
    (OptoNumberError, "OptoNumberError"),
    (OptoParserError, "OptoParserError"),
    (PathTypeError, "PathTypeError"),
    (PathFileError, "PathFileError"),
    # Exceptions PostgresDjangoUpsert
    (PostgresKeyError, "PostgresKeyError"),
    (PostgresTypeError, "PostgresTypeError"),
    (IntegrityError, "IntegrityError (probably supplier None)"),
)


def _exception_label(except_error: Exception) -> str:
    """Libellé journalisé d'une exception : celui de la première classe attendue qui lui.

    correspond, sinon "Exception Générale"
    :param except_error: exception levée pendant l'import.
    """
    return next(
        (label for klass, label in LOGGED_EXCEPTIONS if isinstance(except_error, klass)),
        "Exception Générale",
    )


def _require_columns(columns_dict: dict) -> None:
    """TypeError si le mapping colonnes EdiImport / fichier est absent de ColumnDefinition.

    Sans ce mapping l'import ne peut pas se faire.
    """
    if not columns_dict:
        raise TypeError("Vous n'avez pas de colonnes à récupérer")


def _raise_file_errors(flow_name: str, source: Path) -> NoReturn:
    """Signale un fichier dont des lignes sont en erreur de validation."""
    raise ValidationError(f"Le fichier comporte des erreurs: {flow_name} - {str(source)!r}")


def make_insert_edi_files(model, flow_name, source, trace, validator, params_dict_loader):
    """Réalise la lecture, transformation du fichier, la validation et l'insertion en base.

    :param model:               model au sens Django
    :param flow_name:           flow_name
    :param source:              Fichier source
    :param trace:               Trace à utiliser
    :param validator:           Validateur des données en entrée
    :param params_dict_loader:  Dictionnaire de paramètres
    :return:
    """
    error = False
    valide_file_io = io.StringIO()
    to_print = ""

    try:
        to_print += f"Import : {flow_name}\n"
        columns_dict = get_columns(ColumnDefinition, flow_name)

        _require_columns(columns_dict)
        flow_dict = get_loader_params_dict(SupplierDefinition, flow_name)
        params_dict_load = {
            **params_dict_loader,
            **flow_dict,
            "trace": trace,
        }
        params_dict_validation = {
            "trace": trace,
            "insert_method": "upsert",
            "validation": (PydanticValidation, PydanticTrace),
            "file_io": valide_file_io,
            "nb_errors_max": 50,
        }

        loader_class = Opto33Loader if flow_name == "Edi" else FileLoader

        with loader_class(
            source=source,
            columns_dict=columns_dict,
            first_line=get_first_line(SupplierDefinition, flow_name),
            params_dict=params_dict_load,
        ) as file_load:
            validation = Validation(
                dict_flow=file_load.read_dict(),
                model=model,
                validator=validator,
                params_dict=params_dict_validation,
            )
            error_lines = validation.validate()

            if error_lines:
                to_print += f"\nLignes en erreur : {error_lines}\n"
                _raise_file_errors(flow_name, source)

            to_print += "\nPas d'erreurs\n"

            postgres_upsert = PostgresDjangoUpsert(
                model=model,
                fields_dict=dict.fromkeys(validator.model_config["include"], False),
                cnx=connection,
                exclude_update_fields=set(),
            )
            valide_file_io.seek(0)
            postgres_upsert.insertion(
                file=valide_file_io,
                insert_mode="insert",
                delimiter=";",
                quote_character='"',
                kwargs_prepared={"trace": trace},
            )

    except Exception as except_error:
        error = True
        label = _exception_label(except_error)
        LOGGER_EDI.exception("%s", label)

    finally:
        if error or trace.errors:
            trace.errors = True
            trace.comment = (
                trace.comment + "\n. Une erreur c'est produite veuillez consulter les logs"
            )

        trace.time_to_process = (timezone.now() - trace.created_at).total_seconds()
        trace.save()

        try:
            if not valide_file_io.closed:
                valide_file_io.close()
            del valide_file_io

        except (AttributeError, NameError):
            pass

    return to_print
