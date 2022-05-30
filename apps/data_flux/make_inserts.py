# pylint: disable=E0401,R0912,R0913,R0914,R0915,W0703,W1203
"""
FR : Module d'insertion des modèles de Sage X3
EN : Insert module for Sage X3 models

Commentaire:

created at: 2022-05-10
created by: Paulo ALVES

modified at: 2022-05-10
modified by: Paulo ALVES
"""
import io

from django.db import connection
from django.utils import timezone

from heron.loggers import LOGGER_IMPORT
from apps.data_flux.validation import Validation, PydanticValidation, PydanticTrace
from apps.data_flux.loader import (
    GetAddDictError,
    IterFileToInsertError,
    ExcelToCsvError,
    FileToCsvError,
    FileLoader,
)
from apps.data_flux.postgres_save import PostgresKeyError, PostgresTypeError, PostgresDjangoUpsert


def make_insert(
    model,
    flow_name,
    source,
    trace,
    validator,
    params_dict_loader,
    extend_model=None,
    insert_mode=None,
):
    """
    Réalise la lecture, transformation du fichier, la validation et l'insertion en base
    :param model:               model au sens Django
    :param flow_name:           flow_name de la trace
    :param source:              Fichier source
    :param trace:               Trace à utiliser
    :param validator:           Validateur des données en entrée
    :param params_dict_loader:  Dictionnaire de paramètres
    :param extend_model:        Si le model est subdivisé ou étendu il faut récupérer get_uniques ou
                                get_columns_import depuis celui-ci
    :param insert_mode:         Mode d'insertion forcé
    """
    error = False
    valide_file_io = io.StringIO()
    to_print = ""

    if extend_model is None:
        get_uniques_set = model.get_uniques()
        get_columns_import_dict = model.get_columns_import()

    else:
        get_uniques_set = extend_model.get_uniques()
        get_columns_import_dict = extend_model.get_columns_import()

    try:
        to_print += f"Import : {flow_name}\n"
        params_dict_validation = {
            "trace": trace,
            "insert_method": insert_mode or "upsert",
            "validation": (PydanticValidation, PydanticTrace),
            "file_io": valide_file_io,
        }
        fields_dict = {
            key: key in get_uniques_set
            for key in {**get_columns_import_dict, **params_dict_loader.get("add_fields_dict")}
        }
        nbre = 2
        with FileLoader(
            source=source,
            columns_dict=get_columns_import_dict,
            params_dict=params_dict_loader,
        ) as file_load:

            validation = Validation(
                dict_flow=file_load.read_dict(),
                model=model,
                validator=validator,
                params_dict=params_dict_validation,
            )
            error_lines = validation.validate()

            postgres_upsert = PostgresDjangoUpsert(
                model=model,
                fields_dict=fields_dict,
                cnx=connection,
                exclude_update_fields={"created_at", "uuid_identification"},
            )

            valide_file_io.seek(0)

            for i, line in enumerate(valide_file_io, 1):
                if i == nbre:
                    break
                print(line, end="")

            valide_file_io.seek(0)

            postgres_upsert.insertion(
                file=valide_file_io,
                insert_mode="upsert",
                delimiter=";",
                quote_character='"',
            )

            if error_lines:
                to_print += f"\nLignes en erreur : {error_lines}\n"
            else:
                to_print += "\nPas d'erreurs\n"

    # Exceptions FileLoader ========================================================================
    except GetAddDictError as except_error:
        error = True
        LOGGER_IMPORT.exception(f"GetAddDictError : {except_error!r}")

    except IterFileToInsertError as except_error:
        error = True
        LOGGER_IMPORT.exception(f"IterFileToInsertError : {except_error!r}")

    except ExcelToCsvError as except_error:
        error = True
        LOGGER_IMPORT.exception(f"ExcelToCsvError : {except_error!r}")

    except FileToCsvError as except_error:
        error = True
        LOGGER_IMPORT.exception(f"FileToCsvError : {except_error!r}")

    # Exceptions PostgresDjangoUpsert ==============================================================
    except PostgresKeyError as except_error:
        error = True
        LOGGER_IMPORT.exception(f"PostgresKeyError : {except_error!r}")

    except PostgresTypeError as except_error:
        error = True
        LOGGER_IMPORT.exception(f"PostgresTypeError : {except_error!r}")

    # Exception Générale ===========================================================================
    except Exception as except_error:
        error = True
        LOGGER_IMPORT.exception(f"Exception Générale : {except_error!r}")

    finally:
        if error:
            trace.errors = True
            trace.comment = (
                trace.comment + "\nUne erreur c'est produite veuillez consulter les logs"
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
