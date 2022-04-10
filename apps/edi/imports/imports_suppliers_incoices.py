# pylint: disable=E0401,R0913,W0703,W1203
"""
FR : Module d'import des factures founisseurs EDI
EN : Import module for EDI incoives suppliers

Commentaire:

created at: 2022-04-08
created by: Paulo ALVES

modified at: 2022-04-08
modified by: Paulo ALVES
"""
import io
from uuid import uuid4
from pathlib import Path

import redis
from django.db import connection
from django.utils import timezone

from apps.core.functions.functions_setups import settings
from apps.edi.loggers import EDI_LOGGER
from apps.edi.models import SupplierDefinition, ColumnDefinition, EdiImport
from apps.edi.parameters.invoices_imports import get_columns, get_first_line, get_loader_params_dict
from apps.edi.forms.forms_djantic.invoices import (
    BbrgBulkSchema,
    EdiSchema,
    EyeConfortSchema,
    GeneriqueSchema,
    HearingSchema,
    IntersonSchema,
    JohnsonSchema,
    LmcSchema,
    NewsonSchema,
    PhonakSchema,
    ProditionSchema,
    SigniaSchema,
    StarkeySchema,
    TechnidisSchema,
    UnitronSchema,
    WidexSchema,
    WidexGaSchema,
)
from apps.data_flux.validation import Validation, PydanticValidation, PydanticTrace
from apps.data_flux.trace import get_trace
from apps.data_flux.loader import (
    GetAddDictError,
    IterFileToInsertError,
    ExcelToCsvError,
    FileToCsvError,
    FileLoader,
)
from apps.data_flux.postgres_save import PostgresKeyError, PostgresTypeError, PostgresDjangoUpsert

try:
    cache = redis.StrictRedis()
except redis.exceptions.ConnectionError:
    cache = {}

proccessing_dir = Path(settings.PROCESSING_SUPPLIERS_DIR)


def get_supplier_name(table_name: str):
    """
    :param table_name: champ table_name dans la table SupplierDefinition
    :return: Retourne le supplier_name du fournisseur dans la table SupplierDefinition
    """
    try:
        name = SupplierDefinition.objects.get(table_name=table_name)

        if isinstance(cache, (dict,)):
            cache[f"{table_name}_supplier"] = name.supplier_name
            cache[f"{table_name}_siret"] = name.supplier_siret
        else:
            cache.set(f"{table_name}_supplier", name.supplier_name)
            cache.set(f"{table_name}_siret", name.supplier_siret)

        return name.supplier_name

    except SupplierDefinition.DoesNotExist:
        return None


def get_supplier_ident(table_name: str):
    """
    :param table_name: champ table_name dans la table SupplierDefinition
    :return: Retourne le supplier_siret du fournisseur dans la table SupplierDefinition
    """
    try:
        name = SupplierDefinition.objects.get(table_name=table_name)

        if isinstance(cache, (dict,)):
            cache[f"{table_name}_siret"] = name.supplier_siret
            cache[f"{table_name}_supplier"] = name.supplier_name
        else:
            cache.set(f"{table_name}_siret", name.supplier_siret)
            cache.set(f"{table_name}_supplier", name.supplier_name)

        return name.supplier_siret

    except SupplierDefinition.DoesNotExist:
        return None


def make_insert(model, flow_name, source, trace, validator, params_dict_loader):
    """
    Réalise la lecture, transformation du fichier, la validation et l'insertion en base
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

    try:
        print("Import : ", flow_name)
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
        columns_dict = get_columns(ColumnDefinition, flow_name)

        with FileLoader(
            source=source,
            columns_dict=columns_dict,
            first_line=get_first_line(SupplierDefinition, flow_name),
            params_dict=params_dict_load,
        ) as file_load:

            for i, line in enumerate(file_load.read_dict(), 1):
                if i == 10:
                    break
                print(line)

            validation = Validation(
                dict_flow=file_load.read_dict(),
                model=model,
                validator=validator,
                params_dict=params_dict_validation,
            )
            error_lines = validation.validate()

            # postgres_upsert = PostgresDjangoUpsert(
            #     model=model,
            #     fields_dict=validator.Config.include,
            #     cnx=connection,
            #     exclude_update_fields={},
            # )

            valide_file_io.seek(0)

            for i, line in enumerate(valide_file_io, 1):
                if i == 10:
                    break
                print(line, end="")

            if error_lines:
                print(
                    "\nLignes en erreur : ",
                    error_lines,
                    "\n======================================================================="
                    "=======================================================================",
                )
            else:
                print(
                    "\nPas d'erreurs",
                    "\n\n======================================================================="
                    "======================================================================="
                )

            valide_file_io.seek(0)

            # postgres_upsert.insertion(
            #     file=valide_file_io,
            #     insert_mode="insert",
            #     delimiter=";",
            #     quote_character='"',
            # )

    # Exceptions FileLoader ========================================================================
    except GetAddDictError as except_error:
        error = True
        EDI_LOGGER.exception(f"GetAddDictError : {except_error!r}")

    except IterFileToInsertError as except_error:
        error = True
        EDI_LOGGER.exception(f"IterFileToInsertError : {except_error!r}")

    except ExcelToCsvError as except_error:
        error = True
        EDI_LOGGER.exception(f"ExcelToCsvError : {except_error!r}")

    except FileToCsvError as except_error:
        error = True
        EDI_LOGGER.exception(f"FileToCsvError : {except_error!r}")

    # Exceptions PostgresDjangoUpsert ==============================================================
    except PostgresKeyError as except_error:
        error = True
        EDI_LOGGER.exception(f"PostgresKeyError : {except_error!r}")

    except PostgresTypeError as except_error:
        error = True
        EDI_LOGGER.exception(f"PostgresTypeError : {except_error!r}")

    # Exception Générale ===========================================================================
    except Exception as except_error:
        error = True
        EDI_LOGGER.exception(f"Exception Générale : {except_error!r}")

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


def bbgr_bulk(file_path: Path):
    """
    Import du fichier des factures BBGR bulk
    :param file_path: Path du fichier à traiter
    """
    model = EdiImport
    validator = BbrgBulkSchema
    file_name = file_path.name
    trace_name = "Import BBGR Bulk"
    application_name = "edi_imports_imports_suppliers_incoices"
    flow_name = "BbrgBulk"
    comment = f"import des factures BBGR Bulk"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "supplier": cache.get("BbgrBulk_supplier") or get_supplier_name("BbgrBulk"),
            "supplier_ident": cache.get("BbgrBulk_siret") or get_supplier_ident("BbgrBulk"),
            "uuid_identification": uuid4(),
        },
    }
    make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)

    return trace


def edi(file_path: Path):
    """
    Import du fichier des factures EDI au format opto33
    :param file_path: Path du fichier à traiter
    """
    model = EdiImport
    validator = EdiSchema
    file_name = file_path.name
    trace_name = "Import Edi"
    application_name = "edi_imports_imports_suppliers_incoices"
    flow_name = "Edi"
    comment = f"import des factures Edi opto 33"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "uuid_identification": uuid4(),
        },
    }
    make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)

    return trace


def eye_confort(file_path: Path):
    """
    Import du fichier des factures EyeConfort
    :param file_path: Path du fichier à traiter
    """
    model = EdiImport
    validator = EyeConfortSchema
    file_name = file_path.name
    trace_name = "Import EyeConfort"
    application_name = "edi_imports_imports_suppliers_incoices"
    flow_name = "EyeConfort"
    comment = f"import des factures EyeConfort"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "supplier": cache.get("EyeConfort_supplier") or get_supplier_name("EyeConfort"),
            "supplier_ident": cache.get("EyeConfort_siret") or get_supplier_ident("EyeConfort"),
            "uuid_identification": uuid4(),
        },
    }
    make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)

    return trace


def generique(file_path: Path):
    """
    Import du fichier des factures au format du cahier des charges Génerique
    :param file_path: Path du fichier à traiter
    """
    model = EdiImport
    validator = GeneriqueSchema
    file_name = file_path.name
    trace_name = "Import Génerique"
    application_name = "edi_imports_imports_suppliers_incoices"
    flow_name = "Generique"
    comment = f"import des factures au format du cahier des charges Génerique"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "uuid_identification": uuid4(),
        },
    }
    make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)

    return trace


def hearing(file_path: Path):
    """
    Import du fichier des factures Hearing
    :param file_path: Path du fichier à traiter
    """
    model = EdiImport
    validator = HearingSchema
    file_name = file_path.name
    trace_name = "Import Hearing"
    application_name = "edi_imports_imports_suppliers_incoices"
    flow_name = "Hearing"
    comment = f"import des factures Hearing"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "supplier_ident": cache.get("Hearing_siret") or get_supplier_ident("Hearing"),
            "uuid_identification": uuid4(),
        },
    }
    make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)

    return trace


def interson(file_path: Path):
    """
    Import du fichier des factures Interson
    :param file_path: Path du fichier à traiter
    """
    model = EdiImport
    validator = IntersonSchema
    file_name = file_path.name
    trace_name = "Import Interson"
    application_name = "edi_imports_imports_suppliers_incoices"
    flow_name = "Interson"
    comment = f"import des factures Interson"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "uuid_identification": uuid4(),
        },
    }
    make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)

    return trace


def johnson(file_path: Path):
    """
    Import du fichier des factures Johnson
    :param file_path: Path du fichier à traiter
    """
    model = EdiImport
    validator = JohnsonSchema
    file_name = file_path.name
    trace_name = "Import Johnson"
    application_name = "edi_imports_imports_suppliers_incoices"
    flow_name = "Johnson"
    comment = f"import des factures Johnson"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "supplier": cache.get("Johnson_supplier") or get_supplier_name("Johnson"),
            "supplier_ident": cache.get("Johnson_siret") or get_supplier_ident("Johnson"),
            "uuid_identification": uuid4(),
        },
        "exclude_rows_dict": {1: "Total"},
    }
    make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)

    return trace


def Lmc(file_path: Path):
    """
    Import du fichier des factures Lmc
    :param file_path: Path du fichier à traiter
    """
    model = EdiImport
    validator = LmcSchema
    file_name = file_path.name
    trace_name = "Import Lmc"
    application_name = "edi_imports_imports_suppliers_incoices"
    flow_name = "Lmc"
    comment = f"import des factures Lmc"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "supplier_ident": cache.get("Lmc_siret") or get_supplier_ident("Lmc"),
            "uuid_identification": uuid4(),
        },
    }
    make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)

    return trace


def newson(file_path: Path):
    """
    Import du fichier des factures Newson
    :param file_path: Path du fichier à traiter
    """
    model = EdiImport
    validator = NewsonSchema
    file_name = file_path.name
    trace_name = "Import Newson"
    application_name = "edi_imports_imports_suppliers_incoices"
    flow_name = "Newson"
    comment = f"import des factures Newson"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "supplier": cache.get("Newson_supplier") or get_supplier_name("Newson"),
            "supplier_ident": cache.get("Newson_siret") or get_supplier_ident("Newson"),
            "uuid_identification": uuid4(),
        },
    }
    make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)

    return trace


def Phonak(file_path: Path):
    """
    Import du fichier des factures Phonak
    :param file_path: Path du fichier à traiter
    """
    model = EdiImport
    validator = PhonakSchema
    file_name = file_path.name
    trace_name = "Import Phonak"
    application_name = "edi_imports_imports_suppliers_incoices"
    flow_name = "Phonak"
    comment = f"import des factures Phonak"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "supplier_ident": cache.get("Phonak_siret") or get_supplier_ident("Phonak"),
            "uuid_identification": uuid4(),
        },
    }
    make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)

    return trace


def prodition(file_path: Path):
    """
    Import du fichier des factures Prodition
    :param file_path: Path du fichier à traiter
    """
    model = EdiImport
    validator = ProditionSchema
    file_name = file_path.name
    trace_name = "Import Prodition"
    application_name = "edi_imports_imports_suppliers_incoices"
    flow_name = "Prodition"
    comment = f"import des factures Prodition"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "supplier_ident": cache.get("Prodition_siret") or get_supplier_ident("Prodition"),
            "uuid_identification": uuid4(),
        },
    }
    make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)

    return trace


def signia(file_path: Path):
    """
    Import du fichier des factures Signia
    :param file_path: Path du fichier à traiter
    """
    model = EdiImport
    validator = SigniaSchema
    file_name = file_path.name
    trace_name = "Import Signia"
    application_name = "edi_imports_imports_suppliers_incoices"
    flow_name = "Signia"
    comment = f"import des factures Signia"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "supplier": cache.get("Signia_supplier") or get_supplier_name("Signia"),
            "supplier_ident": cache.get("Signia_siret") or get_supplier_ident("Signia"),
            "uuid_identification": uuid4(),
        },
    }
    make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)

    return trace


def starkey(file_path: Path):
    """
    Import du fichier des factures Starkey
    :param file_path: Path du fichier à traiter
    """
    model = EdiImport
    validator = StarkeySchema
    file_name = file_path.name
    trace_name = "Import Starkey"
    application_name = "edi_imports_imports_suppliers_incoices"
    flow_name = "Starkey"
    comment = f"import des factures Starkey"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "supplier_ident": cache.get("Starkey_siret") or get_supplier_ident("Starkey"),
            "uuid_identification": uuid4(),
        },
    }
    make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)

    return trace


def technidis(file_path: Path):
    """
    Import du fichier des factures Technidis
    :param file_path: Path du fichier à traiter
    """
    model = EdiImport
    validator = TechnidisSchema
    file_name = file_path.name
    trace_name = "Import Technidis"
    application_name = "edi_imports_imports_suppliers_incoices"
    flow_name = "Technidis"
    comment = f"import des factures Technidis"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "uuid_identification": uuid4(),
        },
    }
    make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)

    return trace


def unitron(file_path: Path):
    """
    Import du fichier des factures Unitron
    :param file_path: Path du fichier à traiter
    """
    model = EdiImport
    validator = UnitronSchema
    file_name = file_path.name
    trace_name = "Import Unitron"
    application_name = "edi_imports_imports_suppliers_incoices"
    flow_name = "Unitron"
    comment = f"import des factures Unitron"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "supplier_ident": cache.get("Unitron_siret") or get_supplier_ident("Unitron"),
            "uuid_identification": uuid4(),
        },
    }
    make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)

    return trace


def widex(file_path: Path):
    """
    Import du fichier des factures Widex
    :param file_path: Path du fichier à traiter
    """
    model = EdiImport
    validator = WidexSchema
    file_name = file_path.name
    trace_name = "Import Widex"
    application_name = "edi_imports_imports_suppliers_incoices"
    flow_name = "Widex"
    comment = f"import des factures Widex"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "supplier_ident": cache.get("Widex_siret") or get_supplier_ident("Widex"),
            "uuid_identification": uuid4(),
        },
    }
    make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)

    return trace


def widex_ga(file_path: Path):
    """
    Import du fichier des factures Widex Grand Audition
    :param file_path: Path du fichier à traiter
    """
    model = EdiImport
    validator = WidexGaSchema
    file_name = file_path.name
    trace_name = "Import WidexGa"
    application_name = "edi_imports_imports_suppliers_incoices"
    flow_name = "WidexGa"
    comment = f"import des factures Widex Grand Audition"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "supplier_ident": cache.get("WidexGa_siret") or get_supplier_ident("WidexGa"),
            "uuid_identification": uuid4(),
        },
    }
    make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)

    return trace
