# pylint: disable=C0303,E0401,W1203,W0703,R0912,R0913,R0914,R0915
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
from pathlib import Path

import redis
from django.utils import timezone
from psycopg2 import sql

from apps.core.functions.functions_setups import settings, connection
from apps.edi.loggers import EDI_LOGGER
from apps.edi.bin.edi_pre_processing_pool import bulk_translate_file
from apps.edi.bin.edi_post_processing_pool import (
    bulk_post_insert,
    bbgr_statment_post_insert,
    edi_post_insert,
    eye_confort_post_insert,
    generique_post_insert,
    hearing_post_insert,
    interson_post_insert,
    johnson_post_insert,
    lmc_post_insert,
    newson_post_insert,
    phonak_post_insert,
    prodition_post_insert,
    signia_post_insert,
    starkey_post_insert,
    technidis_post_insert,
    unitron_post_insert,
    widex_post_insert,
    widexga_post_insert,
)
from apps.edi.models import SupplierDefinition, ColumnDefinition, EdiImport
from apps.edi.parameters.invoices_imports import get_columns, get_first_line, get_loader_params_dict
from apps.edi.forms.forms_djantic.forms_invoices import (
    BbgrBulkSchema,
    BbgrStatmentSchema,
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


def get_suppliers(flow_name: str):
    """
    :param flow_name: champ flow_name dans la table SupplierDefinition
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


def get_supplier_name(flow_name: str):
    """
    :param flow_name: champ flow_name dans la table SupplierDefinition
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


def get_supplier_ident(flow_name: str):
    """
    :param flow_name: champ flow_name dans la table SupplierDefinition
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


def get_supplier(flow_name):
    """Get supplier name in cache ou model SupplierDefinition"""
    return (
        cache.get(f"{flow_name}_supplier").decode() if cache.get(f"{flow_name}") else None
    ) or get_supplier_name(flow_name)


def get_ident(flow_name):
    """Get supplier ident in cache ou model SupplierDefinition"""
    return (
        cache.get(f"{flow_name}_ident").decode() if cache.get(f"{flow_name}") else None
    ) or get_supplier_ident(flow_name)


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

            else:
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
            )

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

    # Exceptions Opto33Loader ======================================================================
    except OptoDateError as except_error:
        error = True
        EDI_LOGGER.exception(f"OptoDateError : {except_error!r}")

    except OptoLinesError as except_error:
        error = True
        EDI_LOGGER.exception(f"OptoLinesError : {except_error!r}")

    except OptoQualifierError as except_error:
        error = True
        EDI_LOGGER.exception(f"OptoQualifierError : {except_error!r}")

    except OptoIdError as except_error:
        error = True
        EDI_LOGGER.exception(f"OptoIdError : {except_error!r}")

    except OptoNumberError as except_error:
        error = True
        EDI_LOGGER.exception(f"OptoNumberError : {except_error!r}")

    except OptoParserError as except_error:
        error = True
        EDI_LOGGER.exception(f"OptoParserError : {except_error!r}")

    except PathTypeError as except_error:
        error = True
        EDI_LOGGER.exception(f"PathTypeError : {except_error!r}")

    except PathFileError as except_error:
        error = True
        EDI_LOGGER.exception(f"PathFileError : {except_error!r}")

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


def bbgr_bulk(file_path: Path):
    """
    Import du fichier des factures BBGR bulk
    :param file_path: Path du fichier à traiter
    """
    model = EdiImport
    validator = BbgrBulkSchema
    file_name = file_path.name
    trace_name = "Import BBGR Bulk"
    application_name = "edi_imports_imports_suppliers_incoices"
    flow_name = "BbgrBulk"
    comment = ""
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "flow_name": flow_name,
            "supplier": get_supplier(flow_name),
            "supplier_ident": get_ident(flow_name),
            "uuid_identification": trace.uuid_identification,
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    new_file_path = bulk_translate_file(file_path)
    to_print = make_insert(model, flow_name, new_file_path, trace, validator, params_dict_loader)
    new_file_path.unlink()
    bulk_post_insert(trace.uuid_identification)

    return trace, to_print


def bbgr_statment(file_path: Path):
    """
    Import du fichier des factures BBGR bulk
    :param file_path: Path du fichier à traiter
    """
    model = EdiImport
    validator = BbgrStatmentSchema
    file_name = file_path.name
    trace_name = "Import BBGR Statment"
    application_name = "edi_imports_imports_suppliers_incoices"
    flow_name = "BbgrStatment"
    comment = ""
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "flow_name": flow_name,
            "supplier": get_supplier(flow_name),
            "supplier_ident": get_ident(flow_name),
            "uuid_identification": trace.uuid_identification,
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    to_print = make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)
    bbgr_statment_post_insert(trace.uuid_identification)

    return trace, to_print


def edi(file_path: Path):
    """
    Import du fichier des factures EDI au format opto33
    :param file_path: Path du fichier à traiter
    """
    model = EdiImport
    validator = EdiSchema
    file_name = file_path.name
    trace_name = "Import Edi - tiers : "
    application_name = "edi_imports_imports_suppliers_incoices"
    flow_name = "Edi"
    comment = ""
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "flow_name": flow_name,
            "uuid_identification": trace.uuid_identification,
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    to_print = make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)
    edi_post_insert(trace.uuid_identification)

    return trace, to_print


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
    comment = ""
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "flow_name": flow_name,
            "supplier": get_supplier(flow_name),
            "supplier_ident": get_ident(flow_name),
            "uuid_identification": trace.uuid_identification,
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    to_print = make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)
    eye_confort_post_insert(trace.uuid_identification)

    return trace, to_print


def generique(file_path: Path):
    """
    Import du fichier des factures au format du cahier des charges Génerique
    :param file_path: Path du fichier à traiter
    """
    model = EdiImport
    validator = GeneriqueSchema
    file_name = file_path.name
    trace_name = "Import Génerique - tiers : "
    application_name = "edi_imports_imports_suppliers_incoices"
    flow_name = "Generique"
    comment = ""
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "flow_name": flow_name,
            "uuid_identification": trace.uuid_identification,
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    to_print = make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)
    generique_post_insert(trace.uuid_identification)

    return trace, to_print


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
    comment = ""
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "flow_name": flow_name,
            "supplier": get_supplier(flow_name),
            "supplier_ident": get_ident(flow_name),
            "uuid_identification": trace.uuid_identification,
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    to_print = make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)
    hearing_post_insert(trace.uuid_identification)

    return trace, to_print


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
    comment = ""
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "flow_name": flow_name,
            "supplier": get_supplier(flow_name),
            "supplier_ident": get_ident(flow_name),
            "uuid_identification": trace.uuid_identification,
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    to_print = make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)
    interson_post_insert(trace.uuid_identification)

    return trace, to_print


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
    comment = ""
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "flow_name": flow_name,
            "supplier": get_supplier(flow_name),
            "supplier_ident": get_ident(flow_name),
            "uuid_identification": trace.uuid_identification,
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
        "exclude_rows_dict": {1: "Total"},
    }
    to_print = make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)
    johnson_post_insert(trace.uuid_identification)

    return trace, to_print


def lmc(file_path: Path):
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
    comment = ""
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "flow_name": flow_name,
            "supplier": get_supplier(flow_name),
            "supplier_ident": get_ident(flow_name),
            "uuid_identification": trace.uuid_identification,
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    to_print = make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)
    lmc_post_insert(trace.uuid_identification)

    return trace, to_print


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
    comment = ""
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "flow_name": flow_name,
            "supplier": get_supplier(flow_name),
            "supplier_ident": get_ident(flow_name),
            "uuid_identification": trace.uuid_identification,
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    to_print = make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)
    newson_post_insert(trace.uuid_identification)

    return trace, to_print


def phonak(file_path: Path):
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
    comment = ""
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "flow_name": flow_name,
            "supplier": get_supplier(flow_name),
            "supplier_ident": get_ident(flow_name),
            "uuid_identification": trace.uuid_identification,
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    to_print = make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)
    phonak_post_insert(trace.uuid_identification)

    return trace, to_print


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
    comment = ""
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "flow_name": flow_name,
            "supplier": get_supplier(flow_name),
            "supplier_ident": get_ident(flow_name),
            "uuid_identification": trace.uuid_identification,
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    to_print = make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)
    prodition_post_insert(trace.uuid_identification)

    return trace, to_print


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
    comment = ""
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "flow_name": flow_name,
            "supplier": get_supplier(flow_name),
            "supplier_ident": get_ident(flow_name),
            "uuid_identification": trace.uuid_identification,
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    to_print = make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)
    signia_post_insert(trace.uuid_identification)

    return trace, to_print


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
    comment = ""
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "flow_name": flow_name,
            "supplier": get_supplier(flow_name),
            "supplier_ident": get_ident(flow_name),
            "uuid_identification": trace.uuid_identification,
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    to_print = make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)
    starkey_post_insert(trace.uuid_identification)

    return trace, to_print


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
    comment = ""
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "flow_name": flow_name,
            "supplier": get_supplier(flow_name),
            "supplier_ident": get_ident(flow_name),
            "uuid_identification": trace.uuid_identification,
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    to_print = make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)
    technidis_post_insert(trace.uuid_identification)

    return trace, to_print


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
    comment = ""
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "flow_name": flow_name,
            "supplier": get_supplier(flow_name),
            "supplier_ident": get_ident(flow_name),
            "uuid_identification": trace.uuid_identification,
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    to_print = make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)
    unitron_post_insert(trace.uuid_identification)

    return trace, to_print


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
    comment = ""
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "flow_name": flow_name,
            "supplier": get_supplier(flow_name),
            "supplier_ident": get_ident(flow_name),
            "uuid_identification": trace.uuid_identification,
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    to_print = make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)
    widex_post_insert(trace.uuid_identification)

    return trace, to_print


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
    comment = ""
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "flow_name": flow_name,
            "supplier": get_supplier(flow_name),
            "supplier_ident": get_ident(flow_name),
            "uuid_identification": trace.uuid_identification,
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    to_print = make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)
    widexga_post_insert(trace.uuid_identification)

    return trace, to_print
