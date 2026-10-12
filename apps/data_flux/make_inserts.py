"""FR : Module d'insertion des modèles de Sage X3.

EN : Insert module for Sage X3 models.

Commentaire:

created at: 2022-05-10
created by: Paulo ALVES

modified at: 2022-05-10
modified by: Paulo ALVES
"""

import io

from django.db import connection
from django.utils import timezone

from apps.data_flux.loader import (
    ExcelToCsvError,
    FileLoader,
    FileToCsvError,
    GetAddDictError,
    IterFileToInsertError,
)
from apps.data_flux.postgres_save import PostgresDjangoUpsert, PostgresKeyError, PostgresTypeError
from apps.data_flux.validation import PydanticTrace, PydanticValidation, Validation
from heron.loggers import LOGGER_IMPORT


def _insert_file(
    model,
    source,
    trace,
    validator,
    params_dict_loader,
    *,
    columns_model,
    insert_mode,
    valide_file_io,
):
    """Lecture, validation puis insertion du fichier ; renvoie les lignes en erreur."""
    get_uniques_set = columns_model.get_uniques()
    get_columns_import_dict = columns_model.get_columns_import()
    params_dict_validation = {
        "trace": trace,
        "insert_method": insert_mode or "upsert",
        "validation": (PydanticValidation, PydanticTrace),
        "file_io": valide_file_io,
    }
    fields_dict = {
        key: key in get_uniques_set
        for key in {
            **get_columns_import_dict,
            **(params_dict_loader.get("add_fields_dict") or {}),
        }
    }

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

        postgres_upsert.insertion(
            file=valide_file_io,
            insert_mode=insert_mode or "upsert",
            delimiter=";",
            quote_character='"',
            kwargs_prepared={"trace": trace},
        )

    return error_lines


def make_insert(
    model,
    flow_name,
    source,
    trace,
    validator,
    params_dict_loader,
    *,
    extend_model=None,
    insert_mode=None,
):
    """Réalise la lecture, transformation du fichier, la validation et l'insertion en base.

    :param model:               model au sens Django
    :param flow_name:           flow_name de la trace
    :param source:              Fichier source
    :param trace:               Trace à utiliser
    :param validator:           Validateur des données en entrée
    :param params_dict_loader:  Dictionnaire de paramètres
    :param extend_model:        Si le model est subdivisé ou étendu il faut récupérer get_uniques ou
                                get_columns_import depuis celui-ci
    :param insert_mode:         Mode d'insertion forcé.
    """
    error = False
    valide_file_io = io.StringIO()
    to_print = f"Import : {flow_name}\n"

    try:
        error_lines = _insert_file(
            model,
            source,
            trace,
            validator,
            params_dict_loader,
            columns_model=extend_model or model,
            insert_mode=insert_mode,
            valide_file_io=valide_file_io,
        )
        to_print = (
            f"Import : {flow_name}\n\nLignes en erreur : {error_lines}\n"
            if error_lines
            else f"Import : {flow_name}\n\nPas d'erreurs\n"
        )

    # Exceptions FileLoader et PostgresDjangoUpsert : journalisées sous leur nom de classe
    except (
        GetAddDictError,
        IterFileToInsertError,
        ExcelToCsvError,
        FileToCsvError,
        PostgresKeyError,
        PostgresTypeError,
    ) as except_error:
        error = True
        LOGGER_IMPORT.exception("%s", type(except_error).__name__)

    except Exception:
        error = True
        LOGGER_IMPORT.exception("Exception Générale")

    finally:
        if error:
            trace.errors = True
            trace.comment = (
                trace.comment or ""
            ) + "\n. Une erreur c'est produite veuillez consulter les logs"

        trace.time_to_process = (timezone.now() - trace.created_at).total_seconds()
        trace.save()
        # StringIO.close() est idempotent : pas de garde ni de suppression de la variable
        valide_file_io.close()

    return to_print
