# pylint: disable=W0703,W1203
"""
FR : Module d'import des factures founisseurs EDI
EN : Import module for EDI incoives suppliers

Commentaire:

created at: 2022-04-08
created by: Paulo ALVES

modified at: 2023-01-01
modified by: Paulo ALVES
"""
from pathlib import Path

from django.utils import timezone

from heron.loggers import LOGGER_EDI
from apps.edi.bin.make_insertion_suppliers_invoices import (
    get_ident,
    get_supplier,
    make_insert_edi_files,
)
from apps.edi.bin.edi_pre_processing_pool import (
    bulk_translate_file,
    interson_translate_file,
    transferts_cosium_file,
    johnson_file,
    z_bu_refac_file,
)
from apps.edi.bin.edi_post_processing_pool import (
    bulk_post_insert,
    cosium_post_insert,
    cosium_achats_post_insert,
    tansferts_cosium_post_insert,
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
    z_bu_refac_post_insert,
)
from apps.edi.models import EdiImport
from apps.edi.forms.forms_djantic.forms_invoices import (
    BbgrBulkSchema,
    CosiumSchema,
    CosiumTransfertSchema,
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
    ZBuRefacSageSchema,
)
from apps.data_flux.trace import get_trace
from apps.edi.bin.edi_post_processing_pool import (
    bbgr_statment_post_insert,
    bbgr_monthly_post_insert,
    bbgr_retours_post_insert,
    bbgr_reception_post_insert,
)
from apps.edi.bin.bbgr_002_statment import insert_bbgr_stament_file
from apps.edi.bin.bbgr_003_monthly import insert_bbgr_monthly_file
from apps.edi.bin.bbgr_004_retours import insert_bbgr_retours_file
from apps.edi.bin.bbgr_005_receptions import insert_bbgr_receptions_file


def bbgr_bulk(file_path: Path):
    """Import du fichier des factures BBGR bulk"""
    model = EdiImport
    validator = BbgrBulkSchema
    file_name = file_path.name
    trace_name = "Import BBGR Bulk"
    application_name = "edi_imports_suppliers_incoices_pool"
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
    to_print = make_insert_edi_files(
        model, flow_name, new_file_path, trace, validator, params_dict_loader
    )
    new_file_path.unlink()
    bulk_post_insert(trace.uuid_identification)

    return trace, to_print


def bbgr_statment():
    """
    Insertion depuis B.I des factures BBGR Statment
    """
    trace_name = "Import BBGR Statment"
    application_name = "edi_imports_suppliers_incoices_pool"
    flow_name = "BbgrStatment"
    comment = ""
    trace = get_trace(
        trace_name,
        "insert into (...) selec ... from heron_bi_factures_billstatement",
        application_name,
        flow_name,
        comment,
    )
    error = False

    try:
        insert_bbgr_stament_file(uuid_identification=trace.uuid_identification)
    except Exception as except_error:
        error = True
        LOGGER_EDI.exception(f"Exception Générale : {except_error!r}")

    if error:
        trace.errors = True
        trace.comment = trace.comment + "\n. Une erreur c'est produite veuillez consulter les logs"

    to_print = f"Import : {flow_name}\n"
    bbgr_statment_post_insert(trace.uuid_identification)

    return trace, to_print


def bbgr_monthly():
    """
    Insertion depuis B.I des factures BBGR Monthly
    """
    trace_name = "Import BBGR Monthly"
    application_name = "edi_imports_suppliers_incoices_pool"
    flow_name = "BbgrMonthly"
    comment = ""
    trace = get_trace(
        trace_name,
        (
            "insert into (...) selec ... from heron_bi_factures_monthlydelivery "
            "where type_article not in ('FRAIS_RETOUR', 'DECOTE')"
        ),
        application_name,
        flow_name,
        comment,
    )
    error = False

    try:
        insert_bbgr_monthly_file(uuid_identification=trace.uuid_identification)
    except Exception as except_error:
        error = True
        LOGGER_EDI.exception(f"Exception Générale : {except_error!r}")

    if error:
        trace.errors = True
        trace.comment = trace.comment + "\n. Une erreur c'est produite veuillez consulter les logs"

    to_print = f"Import : {flow_name}\n"
    bbgr_monthly_post_insert(trace.uuid_identification)

    return trace, to_print


def bbgr_retours():
    """
    Insertion depuis B.I des factures Monthly Retours
    """
    trace_name = "Import BBGR Retours"
    application_name = "edi_imports_suppliers_incoices_pool"
    flow_name = "BbgrRetours"
    comment = ""
    trace = get_trace(
        trace_name,
        (
            "insert into (...) selec ... from heron_bi_factures_monthlydelivery "
            "where type_article in ('FRAIS_RETOUR', 'DECOTE')"
        ),
        application_name,
        flow_name,
        comment,
    )
    error = False

    try:
        insert_bbgr_retours_file(uuid_identification=trace.uuid_identification)
    except Exception as except_error:
        error = True
        LOGGER_EDI.exception(f"Exception Générale : {except_error!r}")

    if error:
        trace.errors = True
        trace.comment = trace.comment + "\n. Une erreur c'est produite veuillez consulter les logs"

    to_print = f"Import : {flow_name}\n"
    bbgr_retours_post_insert(trace.uuid_identification)

    return trace, to_print


def bbgr_receptions():
    """
    Insertion depuis B.I des factures BBGR Monthly
    """
    trace_name = "Import BBGR Receptions"
    application_name = "edi_imports_suppliers_incoices_pool"
    flow_name = "BbgrReceptions"
    comment = ""
    trace = get_trace(
        trace_name,
        "insert into (...) selec ... from heron_bi_receptions_bbgr ",
        application_name,
        flow_name,
        comment,
    )
    error = False

    try:
        insert_bbgr_receptions_file(uuid_identification=trace.uuid_identification)
    except Exception as except_error:
        error = True
        LOGGER_EDI.exception(f"Exception Générale : {except_error!r}")

    if error:
        trace.errors = True
        trace.comment = trace.comment + "\n. Une erreur c'est produite veuillez consulter les logs"

    to_print = f"Import : {flow_name}\n"
    bbgr_reception_post_insert(trace.uuid_identification)

    return trace, to_print


def cosium(file_path: Path):
    """Import du fichier des factures Cosium"""
    model = EdiImport
    validator = CosiumSchema
    file_name = file_path.name
    trace_name = "Import Cosium"
    application_name = "edi_imports_suppliers_incoices_pool"
    flow_name = "Cosium"
    comment = ""
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "flow_name": flow_name,
            "supplier": get_supplier(flow_name),
            "uuid_identification": trace.uuid_identification,
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    to_print = make_insert_edi_files(
        model, flow_name, file_path, trace, validator, params_dict_loader
    )
    cosium_post_insert(trace.uuid_identification)

    return trace, to_print


def cosium_achats(file_path: Path):
    """Import du fichier des factures Cosium"""
    model = EdiImport
    validator = CosiumSchema
    file_name = file_path.name
    trace_name = "Import Cosium Achats"
    application_name = "edi_imports_suppliers_incoices_pool"
    flow_name = "CosiumAchats"
    comment = ""
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "flow_name": flow_name,
            "supplier": get_supplier(flow_name),
            "uuid_identification": trace.uuid_identification,
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    to_print = make_insert_edi_files(
        model, flow_name, file_path, trace, validator, params_dict_loader
    )
    cosium_achats_post_insert(trace.uuid_identification)

    return trace, to_print


def transfert_cosium(file_path: Path):
    """Import du fichier des factures Cosium"""
    model = EdiImport
    validator = CosiumTransfertSchema
    file_name = file_path.name
    trace_name = "Import Transferts Cosium"
    application_name = "edi_imports_suppliers_incoices_pool"
    flow_name = "Transfert"
    comment = ""
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "flow_name": flow_name,
            "supplier": get_supplier(flow_name),
            "uuid_identification": trace.uuid_identification,
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    new_file_path = transferts_cosium_file(file_path)
    to_print = make_insert_edi_files(
        model, flow_name, new_file_path, trace, validator, params_dict_loader
    )
    tansferts_cosium_post_insert(trace.uuid_identification)

    return trace, to_print


def edi(file_path: Path):
    """Import du fichier des factures EDI au format opto33"""
    model = EdiImport
    validator = EdiSchema
    file_name = file_path.name
    trace_name = "Import Edi - tiers : "
    application_name = "edi_imports_suppliers_incoices_pool"
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
    trace.save()
    to_print = make_insert_edi_files(
        model, flow_name, file_path, trace, validator, params_dict_loader
    )
    edi_post_insert(trace.uuid_identification)

    return trace, to_print


def eye_confort(file_path: Path):
    """Import du fichier des factures EyeConfort"""
    model = EdiImport
    validator = EyeConfortSchema
    file_name = file_path.name
    trace_name = "Import EyeConfort"
    application_name = "edi_imports_suppliers_incoices_pool"
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
    to_print = make_insert_edi_files(
        model, flow_name, file_path, trace, validator, params_dict_loader
    )
    eye_confort_post_insert(trace.uuid_identification)

    return trace, to_print


def generique(file_path: Path):
    """Import du fichier des factures au format du cahier des charges Génerique"""
    model = EdiImport
    validator = GeneriqueSchema
    file_name = file_path.name
    trace_name = "Import Génerique - tiers : "
    application_name = "edi_imports_suppliers_incoices_pool"
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
    to_print = make_insert_edi_files(
        model, flow_name, file_path, trace, validator, params_dict_loader
    )
    trace.save()
    generique_post_insert(trace.uuid_identification)

    return trace, to_print


def hearing(file_path: Path):
    """Import du fichier des factures Hearing"""
    model = EdiImport
    validator = HearingSchema
    file_name = file_path.name
    trace_name = "Import Hearing"
    application_name = "edi_imports_suppliers_incoices_pool"
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
    to_print = make_insert_edi_files(
        model, flow_name, file_path, trace, validator, params_dict_loader
    )
    hearing_post_insert(trace.uuid_identification)

    return trace, to_print


def interson(file_path: Path):
    """Import du fichier des factures Interson"""
    model = EdiImport
    validator = IntersonSchema
    file_name = file_path.name
    trace_name = "Import Interson"
    application_name = "edi_imports_suppliers_incoices_pool"
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
    new_file_path = interson_translate_file(file_path)
    to_print = make_insert_edi_files(
        model, flow_name, new_file_path, trace, validator, params_dict_loader
    )
    interson_post_insert(trace.uuid_identification)

    return trace, to_print


def johnson(file_path: Path):
    """Import du fichier des factures Johnson"""
    model = EdiImport
    validator = JohnsonSchema
    file_name = file_path.name
    trace_name = "Import Johnson"
    application_name = "edi_imports_suppliers_incoices_pool"
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
    new_file = johnson_file(file_path)
    to_print = make_insert_edi_files(
        model, flow_name, new_file, trace, validator, params_dict_loader
    )
    johnson_post_insert(trace.uuid_identification)
    new_file.unlink()

    return trace, to_print


def lmc(file_path: Path):
    """Import du fichier des factures Lmc"""
    model = EdiImport
    validator = LmcSchema
    file_name = file_path.name
    trace_name = "Import Lmc"
    application_name = "edi_imports_suppliers_incoices_pool"
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
    to_print = make_insert_edi_files(
        model, flow_name, file_path, trace, validator, params_dict_loader
    )
    lmc_post_insert(trace.uuid_identification)

    return trace, to_print


def newson(file_path: Path):
    """Import du fichier des factures Newson"""
    model = EdiImport
    validator = NewsonSchema
    file_name = file_path.name
    trace_name = "Import Newson"
    application_name = "edi_imports_suppliers_incoices_pool"
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
    to_print = make_insert_edi_files(
        model, flow_name, file_path, trace, validator, params_dict_loader
    )
    newson_post_insert(trace.uuid_identification)

    return trace, to_print


def phonak(file_path: Path):
    """Import du fichier des factures Phonak"""
    model = EdiImport
    validator = PhonakSchema
    file_name = file_path.name
    trace_name = "Import Phonak"
    application_name = "edi_imports_suppliers_incoices_pool"
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
    to_print = make_insert_edi_files(
        model, flow_name, file_path, trace, validator, params_dict_loader
    )
    phonak_post_insert(trace.uuid_identification)

    return trace, to_print


def prodition(file_path: Path):
    """Import du fichier des factures Prodition"""
    model = EdiImport
    validator = ProditionSchema
    file_name = file_path.name
    trace_name = "Import Prodition"
    application_name = "edi_imports_suppliers_incoices_pool"
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
    to_print = make_insert_edi_files(
        model, flow_name, file_path, trace, validator, params_dict_loader
    )
    prodition_post_insert(trace.uuid_identification)

    return trace, to_print


def signia(file_path: Path):
    """Import du fichier des factures Signia"""
    model = EdiImport
    validator = SigniaSchema
    file_name = file_path.name
    trace_name = "Import Signia"
    application_name = "edi_imports_suppliers_incoices_pool"
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
    to_print = make_insert_edi_files(
        model, flow_name, file_path, trace, validator, params_dict_loader
    )
    signia_post_insert(trace.uuid_identification)

    return trace, to_print


def starkey(file_path: Path):
    """Import du fichier des factures Starkey"""
    model = EdiImport
    validator = StarkeySchema
    file_name = file_path.name
    trace_name = "Import Starkey"
    application_name = "edi_imports_suppliers_incoices_pool"
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
    to_print = make_insert_edi_files(
        model, flow_name, file_path, trace, validator, params_dict_loader
    )
    starkey_post_insert(trace.uuid_identification)

    return trace, to_print


def technidis(file_path: Path):
    """Import du fichier des factures Technidis"""
    model = EdiImport
    validator = TechnidisSchema
    file_name = file_path.name
    trace_name = "Import Technidis"
    application_name = "edi_imports_suppliers_incoices_pool"
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
    to_print = make_insert_edi_files(
        model, flow_name, file_path, trace, validator, params_dict_loader
    )
    technidis_post_insert(trace.uuid_identification)

    return trace, to_print


def unitron(file_path: Path):
    """Import du fichier des factures Unitron"""
    model = EdiImport
    validator = UnitronSchema
    file_name = file_path.name
    trace_name = "Import Unitron"
    application_name = "edi_imports_suppliers_incoices_pool"
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
    to_print = make_insert_edi_files(
        model, flow_name, file_path, trace, validator, params_dict_loader
    )
    unitron_post_insert(trace.uuid_identification)

    return trace, to_print


def widex(file_path: Path):
    """Import du fichier des factures Widex"""
    model = EdiImport
    validator = WidexSchema
    file_name = file_path.name
    trace_name = "Import Widex"
    application_name = "edi_imports_suppliers_incoices_pool"
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
    to_print = make_insert_edi_files(
        model, flow_name, file_path, trace, validator, params_dict_loader
    )
    widex_post_insert(trace.uuid_identification)

    return trace, to_print


def widex_ga(file_path: Path):
    """Import du fichier des factures Widex Grand Audition"""
    model = EdiImport
    validator = WidexGaSchema
    file_name = file_path.name
    trace_name = "Import WidexGa"
    application_name = "edi_imports_suppliers_incoices_pool"
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
    to_print = make_insert_edi_files(
        model, flow_name, file_path, trace, validator, params_dict_loader
    )
    widexga_post_insert(trace.uuid_identification)

    return trace, to_print


def z_bu_refac(file_path: Path):
    """Import du fichier de la requête sql pour les BU Refac0 extrait de sage"""
    model = EdiImport
    validator = ZBuRefacSageSchema
    file_name = file_path.name
    trace_name = "Import ZBuRefacSage"
    application_name = "edi_imports_suppliers_incoices_pool"
    flow_name = "Zburefac"
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
    new_file = z_bu_refac_file(file_path)
    to_print = make_insert_edi_files(
        model, flow_name, new_file, trace, validator, params_dict_loader
    )
    z_bu_refac_post_insert(trace.uuid_identification)
    new_file.unlink()

    return trace, to_print
