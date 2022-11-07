# pylint: disable=E0401,R0912,R0913,R0914,R0915,W0703,W1203
"""
FR : Module d'import des modèles de Sage X3
EN : Import module for Sage X3 models

Commentaire:

created at: 2022-05-10
created by: Paulo ALVES

modified at: 2022-05-10
modified by: Paulo ALVES
"""
from uuid import uuid4
from pathlib import Path

from django.utils import timezone

from apps.core.functions.functions_setups import settings
from apps.data_flux.make_inserts import make_insert
from apps.book.models import (
    BprBookSage,
    BpsBookSage,
    BpcBookSage,
    BookAdressesSage,
    CodeContactsSage,
    BookContactsSage,
    BookBanksSage,
)
from apps.book.forms.forms_djantic.sage import (
    BprBookSageSchema,
    BpsBookSageSchema,
    BpcBookSageSchema,
    BookAdressesSageSchema,
    CodeContactsSageSchema,
    BookContactsSageSchema,
    BookBanksSageSchema,
)
from apps.book.bin.book_pre_processing import (
    bp_book_pre_processing,
    society_book_pre_processing,
    bank_book_pre_processing,
)
from apps.book.bin.book_post_processing import bpr_book_post_processing
from apps.data_flux.trace import get_trace

proccessing_dir = Path(settings.PROCESSING_SAGE_DIR)


def bpr_sage(file_path: Path):
    """
    Import du fichier des Tiers généraux Sage X3
    :param file_path: Path du fichier à traiter
    """
    base_model = BprBookSage
    extend_model = base_model
    model = base_model.model
    validator = BprBookSageSchema
    file_name = file_path.name
    trace_name = "Mise à jour Tiers BPR Sage"
    application_name = "book_imports_import_sage"
    flow_name = "bpr_sage"
    comment = f"import journalier {file_name} des Tiers Sage"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    to_print = make_insert(
        model, flow_name, file_path, trace, validator, params_dict_loader, extend_model
    )
    bpr_book_post_processing()
    return trace, to_print


def bps_sage(file_path: Path):
    """
    Import du fichier des Tiers Fournisseurs Sage X3
    :param file_path: Path du fichier à traiter
    """
    base_model = BpsBookSage
    extend_model = base_model
    model = base_model.model
    validator = BpsBookSageSchema
    file_name = file_path.name
    trace_name = "Mise à jour Tiers BPS Sage"
    application_name = "book_imports_import_sage"
    flow_name = "bps_sage"
    comment = f"import journalier {file_name} des Tiers Fournisseurs Sage"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    bp_book_pre_processing(proccessing_dir, file_path)
    to_print = make_insert(
        model, flow_name, file_path, trace, validator, params_dict_loader, extend_model
    )

    return trace, to_print


def bpc_sage(file_path: Path):
    """
    Import du fichier des Tiers Clients Sage X3
    :param file_path: Path du fichier à traiter
    """
    base_model = BpcBookSage
    extend_model = base_model
    model = base_model.model
    validator = BpcBookSageSchema
    file_name = file_path.name
    trace_name = "Mise à jour Tiers BPC Sage"
    application_name = "book_imports_import_sage"
    flow_name = "bpc_sage"
    comment = f"import journalier {file_name} des Tiers Clients Sage"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    bp_book_pre_processing(proccessing_dir, file_path)
    to_print = make_insert(
        model, flow_name, file_path, trace, validator, params_dict_loader, extend_model
    )

    return trace, to_print


def adress_sage(file_path: Path):
    """
    Import du fichier des Adresses Tiers Sage X3
    :param file_path: Path du fichier à traiter
    """
    base_model = BookAdressesSage
    extend_model = base_model
    model = base_model.model
    validator = BookAdressesSageSchema
    file_name = file_path.name
    trace_name = "Mise à jour Adresses Tiers BPC Sage"
    application_name = "book_imports_import_sage"
    flow_name = "adress_sage"
    comment = f"import journalier {file_name} des Adresses Tiers Sage"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    society_book_pre_processing(proccessing_dir, file_path)
    to_print = make_insert(
        model,
        flow_name,
        file_path,
        trace,
        validator,
        params_dict_loader,
        extend_model=extend_model,
    )

    return trace, to_print


def code_contact_sage(file_path: Path):
    """
    Import du fichier des Codes Contacts Tiers Sage X3
    :param file_path: Path du fichier à traiter
    """
    base_model = CodeContactsSage
    extend_model = base_model
    model = base_model.model
    validator = CodeContactsSageSchema
    file_name = file_path.name
    trace_name = "Mise à jour Codes Contacts Tiers BPC Sage"
    application_name = "book_imports_import_sage"
    flow_name = "code_contact_sage"
    comment = f"import journalier {file_name} des Codes Contacts Tiers Sage"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
            "uuid_identification": (uuid4, {}),
        },
    }
    society_book_pre_processing(proccessing_dir, file_path)
    to_print = make_insert(
        model, flow_name, file_path, trace, validator, params_dict_loader, extend_model
    )

    return trace, to_print


def contact_sage(file_path: Path):
    """
    Import du fichier des Contacts Tiers Sage X3
    :param file_path: Path du fichier à traiter
    """
    base_model = BookContactsSage
    extend_model = base_model
    model = base_model.model
    validator = BookContactsSageSchema
    file_name = file_path.name
    trace_name = "Mise à jour Contacts Tiers BPC Sage"
    application_name = "book_imports_import_sage"
    flow_name = "contact_sage"
    comment = f"import journalier {file_name} des Contacts Tiers Sage"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
            "uuid_identification": (uuid4, {}),
        },
    }
    society_book_pre_processing(proccessing_dir, file_path)
    to_print = make_insert(
        model, flow_name, file_path, trace, validator, params_dict_loader, extend_model
    )

    return trace, to_print


def bank_sage(file_path: Path):
    """
    Import du fichier des Banques Tiers Sage X3
    :param file_path: Path du fichier à traiter
    """
    base_model = BookBanksSage
    extend_model = base_model
    model = base_model.model
    validator = BookBanksSageSchema
    file_name = file_path.name
    trace_name = "Mise à jour Banques Tiers BPC Sage"
    application_name = "book_imports_import_sage"
    flow_name = "bank_sage"
    comment = f"import journalier {file_name} des Banques Tiers Sage"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    bank_book_pre_processing(proccessing_dir, file_path)
    to_print = make_insert(
        model, flow_name, file_path, trace, validator, params_dict_loader, extend_model
    )

    return trace, to_print
