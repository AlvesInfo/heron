# pylint: disable=W0703,W1203
"""
FR : Module d'import en boucle des modèles de Sage X3
EN : Loop import module for Sage X3 models

Commentaire:

created at: 2022-04-08
created by: Paulo ALVES

modified at: 2022-04-08
modified by: Paulo ALVES
"""
import shutil
from pathlib import Path

from heron.loggers import LOGGER_IMPORT
from apps.core.functions.functions_setups import settings
from apps.book.imports.imports_sage import (
    bpr_sage,
    bps_sage,
    bpc_sage,
    adress_sage,
    code_contact_sage,
    bank_sage,
)
from apps.book.imports.excel_generations import writre_book_files

processing_dict = {
    "ZBIBPR_journalier.heron": bpr_sage,
    "ZBIBPS_journalier.heron": bps_sage,
    "ZBIBPC_journalier.heron": bpc_sage,
    "ZBIADDR_journalier.heron": adress_sage,
    "ZBICONTACT_journalier.heron": code_contact_sage,
    "ZBIBANK_journalier.heron": bank_sage,
}


def get_processing_files():
    """Récupération des fichiers Sage à intégrer, depuis le serveur Sage X3"""
    pre_file_list = list(processing_dict)

    for file in Path(settings.ACUITIS_ARCHIVE_EM_DIR).glob("*"):
        if file.name in processing_dict:
            destination = Path(settings.PROCESSING_SAGE_DIR) / file.name
            shutil.move(file.resolve(), destination.resolve())
            pre_file_list.insert(pre_file_list.index(file.name), destination)

    return [file_to_insert for file_to_insert in pre_file_list if Path(file_to_insert).is_file()]


def process():
    """
    Intégration des fichiers en fonction des fichiers présents dans le répertoire de processing/sage
    """
    processing_files = get_processing_files()

    for file in processing_files:
        error = False
        trace = None

        try:
            trace, _ = processing_dict.get(file.name)(file)
            destination = Path(settings.BACKUP_SAGE_DIR) / file.name
            shutil.move(file.resolve(), destination.resolve())

        except TypeError as except_error:
            error = True
            LOGGER_IMPORT.exception(f"TypeError : {except_error!r}")

        except Exception as except_error:
            error = True
            LOGGER_IMPORT.exception(f"Exception Générale: {file.name}\n{except_error!r}")

        finally:
            if error and trace:
                trace.errors = True
                trace.comment = (
                    trace.comment + "\n. Une erreur c'est produite veuillez consulter les logs"
                )

            if trace is not None:
                trace.save()

    try:
        writre_book_files()
    except Exception as except_error:
        LOGGER_IMPORT.exception(f"Exception Générale: writre_book_files()\n{except_error!r}")


if __name__ == "__main__":
    process()
