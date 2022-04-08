# pylint: disable=E0401,R0903,R0913,W0703,W1203
"""
FR : Module d'import des modèles de Sage X3
EN : Import module for Sage X3 models

Commentaire:

created at: 2022-04-08
created by: Paulo ALVES

modified at: 2022-04-08
modified by: Paulo ALVES
"""
import io
from uuid import uuid4
from pathlib import Path

from django.db import connection
from django.utils import timezone

from apps.core.functions.functions_setups import settings
from apps.accountancy.loggers import IMPORT_LOGGER
from apps.accountancy.models import (
    AccountSage,
    AxeSage,
    SectionSage,
    VatRegimeSage,
    VatSage,
    VatRatSage,
    PaymentCondition,
    TabDivSage,
    CategorySage,
)
from apps.accountancy.forms.forms_djantic.sage import (
    AccountSageSchema,
    AxeSageSchema,
    SectionSageSchema,
    VatRegimeSageSchema,
    VatSageSchema,
    VatRatSageSchema,
    PaymentConditionSchema,
    TabDivSageSchema,
    CategorySageSchema,
)
from apps.data_flux.validation import Validation, PydanticValidation, PydanticTrace
from apps.data_flux.models import Trace
from apps.data_flux.loader import (
    GetAddDictError,
    IterFileToInsertError,
    ExcelToCsvError,
    FileToCsvError,
    FileLoader,
)
from apps.data_flux.postgres_save import PostgresKeyError, PostgresTypeError, PostgresDjangoUpsert

proccessing_dir = Path(settings.PROCESSING_SAGE_DIR)


def get_trace(trace_name, file_name, application_name, flow_name, comment):
    """
    Créé la base de la trace
    :param trace_name: trace_name
    :param file_name: file_name
    :param application_name: application_name
    :param flow_name: flow_name
    :param comment: comment
    :return: Trace Object
    """
    trace = Trace.objects.create(
        created_at=timezone.now(),
        uuid_identification=uuid4(),
        trace_name=trace_name,
        file_name=file_name,
        application_name=application_name,
        flow_name=flow_name,
        comment=comment,
        created_numbers_records=0,
        updated_numbers_records=0,
        errors_numbers_records=0,
        unknown_numbers_records=0,
    )
    return trace


def make_insert(model, source, trace, validator, params_dict_loader, valide_file_io):
    """
    Realise l'insertion
    :param model:
    :param source:
    :param trace:
    :param validator:
    :param params_dict_loader:
    :param valide_file_io:
    :return:
    """
    error = False

    try:
        params_dict_validation = {
            "trace": trace,
            "insert_method": "upsert",
            "validation": (PydanticValidation, PydanticTrace),
            "file_io": valide_file_io,
        }
        fields_dict = {
            key: key in model.get_uniques()
            for key in {**model.get_columns_import(), **params_dict_loader.get("add_fields_dict")}
        }

        with FileLoader(
            source=source,
            columns_dict=model.get_columns_import(),
            params_dict=params_dict_loader,
        ) as file_load:

            # print(fields_dict)
            # for line in file_load.read_dict():
            #     print(line)

            validation = Validation(
                dict_flow=file_load.read_dict(),
                model=model,
                validator=validator,
                params_dict=params_dict_validation,
            )
            error_lines = validation.validate()

            if error_lines:
                print(error_lines)

            postgres_upsert = PostgresDjangoUpsert(
                model=model,
                fields_dict=fields_dict,
                cnx=connection,
                exclude_update_fields={"created_at", "uuid_identification"},
            )

            valide_file_io.seek(0)

            # for line in valide_file_io:
            #     print(line, end="")
            #
            # valide_file_io.seek(0)

            postgres_upsert.insertion(
                file=valide_file_io,
                insert_mode="upsert",
                delimiter=";",
                quote_character='"',
            )

    # Exceptions FileLoader ========================================================================
    except GetAddDictError as except_error:
        error = True
        IMPORT_LOGGER.exception(f"GetAddDictError : {except_error!r}")

    except IterFileToInsertError as except_error:
        error = True
        IMPORT_LOGGER.exception(f"IterFileToInsertError : {except_error!r}")

    except ExcelToCsvError as except_error:
        error = True
        IMPORT_LOGGER.exception(f"ExcelToCsvError : {except_error!r}")

    except FileToCsvError as except_error:
        error = True
        IMPORT_LOGGER.exception(f"FileToCsvError : {except_error!r}")

    # Exceptions PostgresDjangoUpsert ==============================================================
    except PostgresKeyError as except_error:
        error = True
        IMPORT_LOGGER.exception(f"PostgresKeyError : {except_error!r}")

    except PostgresTypeError as except_error:
        error = True
        IMPORT_LOGGER.exception(f"PostgresTypeError : {except_error!r}")

    # Exception Générale ===========================================================================
    except Exception as except_error:
        error = True
        IMPORT_LOGGER.exception(f"Exception Générale : {except_error!r}")

    finally:
        if error:
            trace.errors = True
            trace.comment = (
                "Une erreur c'est produite veuillez consulter les logs\n" + trace.comment
            )

        trace.time_to_process = (timezone.now() - trace.created_at).total_seconds()
        trace.save()


def account_sage(file_path: Path):
    """
    Import du fichier des comptes comptable Sage X3
    :param file_path: Path du fichier à traiter
    """
    model = AccountSage
    validator = AccountSageSchema
    file_name = file_path.name
    trace_name = "Mise à jour Comptes Sage"
    application_name = "accountacy_imports_import_sage"
    flow_name = "AccountSage"
    comment = f"import journalier {file_name} des Comptes comptables Sage"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    valide_file_io = io.StringIO()
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
            "uuid_identification": (uuid4, {}),
        },
    }
    make_insert(model, file_path, trace, validator, params_dict_loader, valide_file_io)

    return trace


def axe_sage(file_path: Path):
    """
    Import du fichier des axes Sage X3
    :param file_path: Path du fichier à traiter
    """
    model = AxeSage
    validator = AxeSageSchema
    file_name = file_path.name
    trace_name = "Mise à jour Axes Sage"
    application_name = "accountacy_imports_import_sage"
    flow_name = "AxeSage"
    comment = f"import journalier {file_name} des Axes Sage"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    valide_file_io = io.StringIO()
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    make_insert(model, file_path, trace, validator, params_dict_loader, valide_file_io)

    return trace


def section_sage(file_path: Path):
    """
    Import du fichier des Sections Sage X3
    :param file_path: Path du fichier à traiter
    """
    model = SectionSage
    validator = SectionSageSchema
    file_name = file_path.name
    trace_name = "Mise à jour Sections Sage"
    application_name = "accountacy_imports_import_sage"
    flow_name = "SectionSage"
    comment = f"import journalier {file_name} des Sections Sage"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    valide_file_io = io.StringIO()
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
            "uuid_identification": (uuid4, {}),
        },
    }
    make_insert(model, file_path, trace, validator, params_dict_loader, valide_file_io)

    return trace


def vat_regime_sage(file_path: Path):
    """
    Import du fichier des Régimes de taxe Sage X3
    :param file_path: Path du fichier à traiter
    """
    model = VatRegimeSage
    validator = VatRegimeSageSchema
    file_name = file_path.name
    trace_name = "Mise à jour Régimes de Taxes Sage"
    application_name = "accountacy_imports_import_sage"
    flow_name = "VatRegimeSage"
    comment = f"import journalier {file_name} des Régimes de taxe Sage"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    valide_file_io = io.StringIO()
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    make_insert(model, file_path, trace, validator, params_dict_loader, valide_file_io)

    return trace


def vat_sage(file_path: Path):
    """
    Import du fichier des Taxes Sage X3
    :param file_path: Path du fichier à traiter
    """
    model = VatSage
    validator = VatSageSchema
    file_name = file_path.name
    trace_name = "Mise à jour Taxes Sage"
    application_name = "accountacy_imports_import_sage"
    flow_name = "VatSage"
    comment = f"import journalier {file_name} des Taxes Sage"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    valide_file_io = io.StringIO()
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    make_insert(model, file_path, trace, validator, params_dict_loader, valide_file_io)

    return trace


def vat_rat_sage(file_path: Path):
    """
    Import du fichier des Taux de Taxes Sage X3
    :param file_path: Path du fichier à traiter
    """
    model = VatRatSage
    validator = VatRatSageSchema
    file_name = file_path.name
    trace_name = "Mise à jour Taux de Taxes Sage"
    application_name = "accountacy_imports_import_sage"
    flow_name = "VatRatSage"
    comment = f"import journalier {file_name} des Taux de Taxes Sage"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    valide_file_io = io.StringIO()
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    make_insert(model, file_path, trace, validator, params_dict_loader, valide_file_io)

    return trace


def payement_condition(file_path: Path):
    """
    Import du fichier des Conditions de paiements Sage X3
    :param file_path: Path du fichier à traiter
    """
    model = PaymentCondition
    validator = PaymentConditionSchema
    file_name = file_path.name
    trace_name = "Mise à jour Conditions de paiements Sage"
    application_name = "accountacy_imports_import_sage"
    flow_name = "PaymentCondition"
    comment = f"import journalier {file_name} des Conditions de paiements Sage"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    valide_file_io = io.StringIO()
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    make_insert(model, file_path, trace, validator, params_dict_loader, valide_file_io)

    return trace


def tab_div_sage(file_path: Path):
    """
    Import du fichier des Tables Diverses Sage X3
    :param file_path: Path du fichier à traiter
    """
    model = TabDivSage
    validator = TabDivSageSchema
    file_name = file_path.name
    trace_name = "Mise à jour Tables Diverses Sage"
    application_name = "accountacy_imports_import_sage"
    flow_name = "TabDivSage"
    comment = f"import journalier {file_name} des Tables Diverses Sage"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    valide_file_io = io.StringIO()
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    make_insert(model, file_path, trace, validator, params_dict_loader, valide_file_io)

    return trace


def category_sage(file_path: Path):
    """
    Import du fichier des Catégories Clients et Fournisseurs Sage X3
    :param file_path: Path du fichier à traiter
    """
    model = CategorySage
    validator = CategorySageSchema
    file_name = file_path.name
    trace_name = "Mise à jour Catégories Clients et Fournisseurs Sage"
    application_name = "accountacy_imports_import_sage"
    flow_name = "CategorySage"
    comment = f"import journalier {file_name} des Catégories Clients et Fournisseurs Sage"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    valide_file_io = io.StringIO()
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    make_insert(model, file_path, trace, validator, params_dict_loader, valide_file_io)

    return trace
