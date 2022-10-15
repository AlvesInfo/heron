# pylint: disable=E0401,W0703,W1203
"""
FR : Module d'import en boucle des fichiers de factures fournisseurs
EN : Loop import module for invoices suppliers files

Commentaire:

created at: 2022-04-09
created by: Paulo ALVES

modified at: 2022-04-09
modified by: Paulo ALVES
"""
import os
import platform
import re
import sys
from pathlib import Path

import django

BASE_DIR = r"C:\SitesWeb\heron"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")
django.setup()

from apps.core.functions.functions_setups import settings
from apps.edi.loggers import EDI_LOGGER
from apps.data_flux.utilities import encoding_detect
from apps.data_flux.postgres_save import get_random_name
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
            # ne sont pas dans la table ColumnDefinition, alors l'import ne peut se faire
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

                raise ValidationError("Le fichier comporte des erreurs")

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


def balance_files(file_path: Path):
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
    comment = "import des factures BBGR Bulk"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "flow_name": flow_name,
            "supplier": get_supplier(flow_name),
            "supplier_ident": get_ident(flow_name),
            "uuid_identification": trace.uuid_identification,
        },
    }
    new_file_path = bulk_translate_file(file_path)
    to_print = make_insert(model, flow_name, new_file_path, trace, validator, params_dict_loader)
    new_file_path.unlink()
    bulk_post_insert(trace.uuid_identification)

    return trace, to_print


def separate_edi():
    """Séparation des fichiers EDI (ex.: JULBO qui met plusieurs edi dans un seul fichier"""
    edi_files_directory = Path(settings.PROCESSING_SUPPLIERS_DIR) / "EDI"

    for file in edi_files_directory.glob("*"):
        encoding = encoding_detect(file) or "ascii"
        una_test = False

        with open(file, "r", encoding=encoding) as edi_file:
            text = edi_file.read().strip()
            split_text = re.split(r"(?=UNA:\+).*[\n|']", text)

            if len(split_text) > 2:
                for text_edi_file in split_text:
                    if text_edi_file:
                        una_test = True
                        file_name = (
                            Path(settings.PROCESSING_SUPPLIERS_DIR)
                            / f"EDI/{file.stem}.{get_random_name()}.edi"
                        )

                        # On s'assure que le nom du fichier n'existe pas
                        while True:
                            if not file_name.is_file():
                                break

                        with open(
                            file_name,
                            "w",
                            encoding=encoding,
                        ) as file_to_write:
                            file_to_write.write(text_edi_file)

        if una_test:
            file.unlink()


def get_files():
    """Retourne la liste des tuples(fichier, process) à traiter"""
    # separate_edi()
    files_directory = Path(settings.PROCESSING_SUPPLIERS_DIR) / directory

    for file in files_directory.glob("*"):
        yield file


def import_files():
    """
    Intégration des balances au format excel
    """
    import time

    start_initial = time.time()

    error = False
    trace = None
    to_print = ""
    for file in get_files():
        try:
            trace, to_print = balance_files(file)
            # destination = Path(settings.BACKUP_SAGE_DIR) / file.name
            # shutil.move(file.resolve(), destination.resolve())

        except TypeError as except_error:
            error = True
            to_print += f"TypeError : {except_error}\n"
            EDI_LOGGER.exception(f"TypeError : {except_error!r}")

        except Exception as except_error:
            error = True
            EDI_LOGGER.exception(f"Exception Générale: {file.name}\n{except_error!r}")

        finally:
            if error and trace:
                trace.errors = True
                trace.comment = (
                    trace.comment + "\n. Une erreur c'est produite veuillez consulter les logs"
                )

            if trace is not None:
                trace.save()

    EDI_LOGGER.warning(
        to_print
        + f"Validation {file.name} in : {time.time() - start_initial} s"
        + "\n\n======================================================================="
        "======================================================================="
    )


def main():
    import_files()


def essais():
    import pandas as pd
    import csv

    from apps.compta.models import PocBalance

    for file in Path(r"C:\ACUITIS\POC_BALANCES").glob("*.xlsx"):
        xl = pd.ExcelFile(file, engine="openpyxl")

        for sheet in xl.sheet_names:
            # print(sheet)
            # print(xl.parse(sheet))
            excel = pd.read_excel(file, sheet_name=sheet, engine="openpyxl")
            csv_file = file.parent / f"{sheet}_{file.stem}.csv"
            excel.to_csv(
                csv_file,
                index=False,
                sep=";",
                line_terminator="\n",
                quoting=csv.QUOTE_ALL,
                encoding="utf8",
            )
            with open(csv_file, "r", encoding="utf8") as file_to_parse:
                print(csv_file.name, sheet)
                csv_reader = csv.reader(file_to_parse, delimiter=";", quotechar='"')
                row = next(csv_reader)
                societe = row[0]
                next(csv_reader)

                # for i, row in enumerate(csv_reader, 3):
                #     print(i, row)
                #     PocBalance.objects.bulk_create(
                #         [
                #             PocBalance(
                #                 societe=societe,
                #                 annee=sheet,
                #                 compte=row[0][:6],
                #                 libelle=row[1],
                #                 solde=row[2],
                #             )
                #         ]
                #     )

                PocBalance.objects.bulk_create(
                    [
                        PocBalance(
                            societe=societe,
                            annee=sheet,
                            compte=row[0][:6],
                            libelle=row[1],
                            solde=row[2] or 0,
                        )
                        for row in csv_reader
                        if row and len(row) > 2 and row[0]
                    ]
                )


if __name__ == "__main__":
    essais()
