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
import shutil
from pathlib import Path
import csv

from apps.core.functions.functions_setups import settings
from apps.edi.loggers import EDI_LOGGER
from apps.edi.imports.imports_suppliers_incoices import (
    bbgr_bulk,
    edi,
    eye_confort,
    generique,
    hearing,
    interson,
    johnson,
    lmc,
    newson,
    phonak,
    prodition,
    signia,
    starkey,
    technidis,
    unitron,
    widex,
    widex_ga,
)
from apps.edi.bin.edi_post_processing import post_processing_all

processing_dict = {
    # "BBRG_BULK": bbgr_bulk,
    "EDI": edi,
    # "EYE_CONFORT": eye_confort,
    # "GENERIQUE": generique,
    # "HEARING": hearing,
    # "INTERSON": interson,
    # "JOHNSON": johnson,
    # "LMC": lmc,
    # "NEWSON": newson,
    # "PHONAK": phonak,
    # "PRODITION": prodition,
    # "SIGNIA": signia,
    # "STARKEY": starkey,
    # "TECHNIDIS": technidis,
    # "UNITRON": unitron,
    # "WIDEX": widex,
    # "WIDEX_GA": widex_ga,
}


def process():
    """
    Intégration des factures fournisseurs présents
    dans le répertoire de processing/suppliers_invoices_files
    """
    import time
    start_initial = time.time()

    for directory, function in processing_dict.items():
        files_directory = Path(settings.PROCESSING_SUPPLIERS_DIR) / directory

        for file in files_directory.glob("*"):
            start = time.time()
            error = False
            trace = None
            to_print = ""

            try:

                trace, to_print = processing_dict.get(directory)(file)
                # destination = Path(settings.BACKUP_SAGE_DIR) / file.name
                # shutil.move(file.resolve(), destination.resolve())

            except TypeError as except_error:
                error = True
                print("TypeError : ", except_error)
                EDI_LOGGER.exception(f"TypeError : {except_error!r}")

            except Exception as except_error:
                error = True
                EDI_LOGGER.exception(f"Exception Générale: {file.name}\n{except_error!r}")

            finally:
                if error and trace:
                    trace.errors = True
                    trace.comment = (
                        trace.comment + "\nUne erreur c'est produite veuillez consulter les logs"
                    )
                    trace.save()

            EDI_LOGGER.warning(
                to_print +
                f" Validation {file.name} in : {time.time() - start} s" 
                "\n\n======================================================================="
                "======================================================================="
            )

    # post_processing_all()

    EDI_LOGGER.warning(f"All validations : {time.time() - start_initial} s")


def main():
    process()


if __name__ == "__main__":
    main()
