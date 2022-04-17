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
from apps.edi.imports.imports_suppliers_incoices_pool import (
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
from apps.edi.bin.edi_post_processing_pool import post_processing_all

processing_dict = {
    "BBRG_BULK": bbgr_bulk,
    "EDI": edi,
    "EYE_CONFORT": eye_confort,
    "GENERIQUE": generique,
    "HEARING": hearing,
    "INTERSON": interson,
    "JOHNSON": johnson,
    "LMC": lmc,
    "NEWSON": newson,
    "PHONAK": phonak,
    "PRODITION": prodition,
    "SIGNIA": signia,
    "STARKEY": starkey,
    "TECHNIDIS": technidis,
    "UNITRON": unitron,
    "WIDEX": widex,
    "WIDEX_GA": widex_ga,
}


def get_files():
    """Retourne la liste des tuples(fichier, process) à traiter"""
    files_list = []

    for directory, function in processing_dict.items():
        files_directory = Path(settings.PROCESSING_SUPPLIERS_DIR) / directory

        for file in files_directory.glob("*"):
            files_list.append((file, function))

    return files_list


def proc_files(process_object):
    """
    Intégration des factures fournisseurs présents
    dans le répertoire de processing/suppliers_invoices_files
    """
    import time
    start_initial = time.time()

    error = False
    trace = None
    to_print = ""
    file, function = process_object

    try:
        trace, to_print = function(file)
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
                trace.comment + "\nUne erreur c'est produite veuillez consulter les logs"
            )
            trace.save()

    EDI_LOGGER.warning(
            to_print + f"Validation {file.name} in : {time.time() - start_initial} s" +
            "\n\n======================================================================="
            "======================================================================="
    )


def loop_proc(proc_files_list):
    """Lancement des process en pool"""
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor() as executor:
        executor.map(proc_files, proc_files_list)

    post_processing_all()


def loop_pool_proc(proc_files_list):
    """Lancement des process en pool"""
    from multiprocessing import Pool

    with Pool(8) as pool:
        pool.map(proc_files, proc_files_list)

    post_processing_all()


def main():
    import time
    start_all = time.time()
    proc_files_l = get_files()
    loop_proc(proc_files_l)
    # loop_pool_proc(proc_files_l)
    print(f"All validations : {time.time() - start_all} s")
    EDI_LOGGER.warning(f"All validations : {time.time() - start_all} s")


if __name__ == "__main__":
    main()
