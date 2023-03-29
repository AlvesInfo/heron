# pylint: disable=C0303,E0401,R0912,R0913,R0914,R0915,W0703,W1203
#
"""
FR : Module d'import des factures founisseurs EDI
EN : Import module for EDI incoives suppliers

Commentaire:

created at: 2022-04-08
created by: Paulo ALVES

modified at: 2023-01-01
modified by: Paulo ALVES
"""
import io
from pathlib import Path
from functools import lru_cache

import redis
from django.utils import timezone
from psycopg2 import sql

from heron.loggers import LOGGER_EDI
from apps.core.functions.functions_setups import settings, connection
from apps.edi.models import SupplierDefinition, ColumnDefinition
from apps.edi.parameters.invoices_imports import get_columns, get_first_line, get_loader_params_dict
from apps.data_flux.validation import Validation, PydanticValidation, PydanticTrace
from apps.data_flux.loader import (
    GetAddDictError,
    IterFileToInsertError,
    ExcelToCsvError,
    FileToCsvError,
    FileLoader,
    Opto33Loader,
)
from apps.data_flux.exceptions import (
    ValidationError,
    OptoDateError,
    OptoLinesError,
    OptoQualifierError,
    OptoIdError,
    OptoNumberError,
    OptoParserError,
    PathTypeError,
    PathFileError,
)
from apps.data_flux.postgres_save import PostgresKeyError, PostgresTypeError, PostgresDjangoUpsert


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
    """
    :param flow_name: Champ flow_name dans la table SupplierDefinition
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
    """
    :param flow_name: Champ flow_name dans la table SupplierDefinition
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
    """
    :param flow_name: Champ flow_name dans la table SupplierDefinition
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


@lru_cache(maxsize=256)
def get_supplier(flow_name):
    """Get supplier name in cache ou model SupplierDefinition"""
    return (
        cache.get(f"{flow_name}_supplier").decode() if cache.get(f"{flow_name}") else None
    ) or get_supplier_name(flow_name)


@lru_cache(maxsize=256)
def get_ident(flow_name):
    """Get supplier ident in cache ou model SupplierDefinition"""
    return (
        cache.get(f"{flow_name}_ident").decode() if cache.get(f"{flow_name}") else None
    ) or get_supplier_ident(flow_name)


def make_insert_edi_files(model, flow_name, source, trace, validator, params_dict_loader):
    """Réalise la lecture, transformation du fichier, la validation et l'insertion en base
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

        if not columns_dict:
            # Si le mapping entre les colonnes de la table EdiImport et les colonnes du fichier,
            # ne sont pas dans la table ColumnDefinition, alors l'import ne peut se faire.
            raise TypeError("Vous n'avez pas de colonnes à récupérer")

        flow_dict = get_loader_params_dict(SupplierDefinition, flow_name)
        params_dict_load = {
            **params_dict_loader,
            **flow_dict,
        }
        params_dict_validation = {
            "trace": trace,
            "insert_method": "upsert",
            "validation": (PydanticValidation, PydanticTrace),
            "file_io": valide_file_io,
            "nb_errors_max": 50,
        }

        if flow_name == "Edi":
            LOADER = Opto33Loader
        else:
            LOADER = FileLoader

        with LOADER(
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
                raise ValidationError(
                    f"Le fichier comporte des erreurs: {flow_name} - {str(source)!r}"
                )

            to_print += "\nPas d'erreurs\n"

            postgres_upsert = PostgresDjangoUpsert(
                model=model,
                fields_dict={key: False for key in validator.Config.include},
                cnx=connection,
                exclude_update_fields={},
            )
            valide_file_io.seek(0)
            postgres_upsert.insertion(
                file=valide_file_io,
                insert_mode="insert",
                delimiter=";",
                quote_character='"',
                kwargs_prepared={"trace": trace},
            )

    # Exceptions FileLoader ========================================================================
    except GetAddDictError as except_error:
        error = True
        LOGGER_EDI.exception(f"GetAddDictError : {except_error!r}")

    except IterFileToInsertError as except_error:
        error = True
        LOGGER_EDI.exception(f"IterFileToInsertError : {except_error!r}")

    except ExcelToCsvError as except_error:
        error = True
        LOGGER_EDI.exception(f"ExcelToCsvError : {except_error!r}")

    except FileToCsvError as except_error:
        error = True
        LOGGER_EDI.exception(f"FileToCsvError : {except_error!r}")

    # Exceptions Opto33Loader ======================================================================
    except OptoDateError as except_error:
        error = True
        LOGGER_EDI.exception(f"OptoDateError : {except_error!r}")

    except OptoLinesError as except_error:
        error = True
        LOGGER_EDI.exception(f"OptoLinesError : {except_error!r}")

    except OptoQualifierError as except_error:
        error = True
        LOGGER_EDI.exception(f"OptoQualifierError : {except_error!r}")

    except OptoIdError as except_error:
        error = True
        LOGGER_EDI.exception(f"OptoIdError : {except_error!r}")

    except OptoNumberError as except_error:
        error = True
        LOGGER_EDI.exception(f"OptoNumberError : {except_error!r}")

    except OptoParserError as except_error:
        error = True
        LOGGER_EDI.exception(f"OptoParserError : {except_error!r}")

    except PathTypeError as except_error:
        error = True
        LOGGER_EDI.exception(f"PathTypeError : {except_error!r}")

    except PathFileError as except_error:
        error = True
        LOGGER_EDI.exception(f"PathFileError : {except_error!r}")

    # Exceptions PostgresDjangoUpsert ==============================================================
    except PostgresKeyError as except_error:
        error = True
        LOGGER_EDI.exception(f"PostgresKeyError : {except_error!r}")

    except PostgresTypeError as except_error:
        error = True
        LOGGER_EDI.exception(f"PostgresTypeError : {except_error!r}")

    # Exception Générale ===========================================================================
    except Exception as except_error:
        error = True
        LOGGER_EDI.exception(f"Exception Générale : {except_error!r}")

    finally:
        if error:
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
