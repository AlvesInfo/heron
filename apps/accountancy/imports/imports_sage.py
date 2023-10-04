# pylint: disable=E0401,R0912,R0913,R0914,R0915,W0703,W1203
"""
FR : Module d'import des modèles de Sage X3
EN : Import module for Sage X3 models

Commentaire:

created at: 2022-04-08
created by: Paulo ALVES

modified at: 2022-04-08
modified by: Paulo ALVES
"""
from uuid import uuid4
from pathlib import Path
import time

from django.utils import timezone

from apps.core.functions.functions_setups import settings
from apps.data_flux.make_inserts import make_insert
from apps.accountancy.bin.sage_pre_processing import mode_reglement_file
from apps.accountancy.models import (
    AccountSage,
    AxeSage,
    SectionSage,
    VatRegimeSage,
    VatSage,
    VatRatSage,
    ModeReglement,
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
    ModeReglementSchema,
    PaymentConditionSchema,
    TabDivSageSchema,
    CategorySageSchema,
)
from apps.data_flux.trace import get_trace

proccessing_dir = Path(settings.PROCESSING_SAGE_DIR)


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
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
            "uuid_identification": (uuid4, {}),
        },
    }
    to_print = make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)

    return trace, to_print


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
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    to_print = make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)

    return trace, to_print


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
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
            "uuid_identification": (uuid4, {}),
        },
    }
    to_print = make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)

    return trace, to_print


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
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
            "uuid_identification": (uuid4, {}),
        },
    }
    to_print = make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)

    return trace, to_print


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
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    to_print = make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)

    return trace, to_print


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
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    time.sleep(5)
    to_print = make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)

    return trace, to_print


def mode_reglement(file_path: Path):
    """
    Import du fichier des Conditions de paiements Sage X3
    :param file_path: Path du fichier à traiter
    """
    model = ModeReglement
    validator = ModeReglementSchema
    file_name = file_path.name
    trace_name = "Mise à jour Mode de règlement Sage"
    application_name = "accountacy_imports_import_sage"
    flow_name = "ModeReglement"
    comment = f"import journalier {file_name} des Mode de règlement Sage"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    file = mode_reglement_file(file_path)
    to_print = make_insert(model, flow_name, file, trace, validator, params_dict_loader)

    return trace, to_print


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
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    to_print = make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)

    return trace, to_print


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
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    to_print = make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)

    return trace, to_print


def category_sage_client(file_path: Path):
    """
    Import du fichier des Catégories Clients et Fournisseurs Sage X3
    :param file_path: Path du fichier à traiter
    """
    model = CategorySage
    validator = CategorySageSchema
    file_name = file_path.name
    trace_name = "Mise à jour Catégories Clients et Fournisseurs Sage"
    application_name = "accountacy_imports_import_sage"
    flow_name = "CategorySageClient"
    comment = f"import journalier {file_name} des Catégories Clients Sage"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    to_print = make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)

    return trace, to_print


def category_sage_supplier(file_path: Path):
    """
    Import du fichier des Catégories Clients et Fournisseurs Sage X3
    :param file_path: Path du fichier à traiter
    """
    model = CategorySage
    validator = CategorySageSchema
    file_name = file_path.name
    trace_name = "Mise à jour Catégories Clients et Fournisseurs Sage"
    application_name = "accountacy_imports_import_sage"
    flow_name = "CategorySageSupplier"
    comment = f"import journalier {file_name} des Catégories Fournisseurs Sage"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    to_print = make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)

    return trace, to_print
