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
from apps.accountancy.imports.imports_sage import (
    account_sage,
    axe_sage,
    section_sage,
    vat_regime_sage,
    vat_sage,
    vat_rat_sage,
    mode_reglement,
    payement_condition,
    tab_div_sage,
    category_sage_client,
    category_sage_supplier,
)
from apps.accountancy.imports.extraction_cct import update_cct_sage
from apps.accountancy.imports.extraction_code_plan import update_code_plan

processing_dict = {
    "ZBIVAT_journalier.heron": vat_sage,
    "ZBIRATVAT_journalier.heron": vat_rat_sage,
    "ZBIACCOUNT_journalier.heron": account_sage,
    "ZBIAXES_journalier.heron": axe_sage,
    "ZBICCE_journalier.heron": section_sage,
    "ZBIMODREG_journalier.heron": mode_reglement,
    "ZBIREG_journalier.heron": vat_regime_sage,
    "ZBIPTE_journalier.heron": payement_condition,
    "ZBIDIV_journalier.heron": tab_div_sage,
    "ZBICATC_journalier.heron": category_sage_client,
    "ZBICATS_journalier.heron": category_sage_supplier,
}


def get_processing_files():
    """Récupération des fichiers Sage à intégrer, depuis le serveur Sage X3"""
    file_list = []

    for file in Path(settings.ACUITIS_ARCHIVE_EM_DIR).glob("*"):
        if file.name in processing_dict:
            destination = Path(settings.PROCESSING_SAGE_DIR) / file.name
            shutil.move(file.resolve(), destination.resolve())
            file_list.append(destination)

    return file_list


def process():
    """
    Intégration des fichiers en fonction des fichiers présents dans le répertoire de processing/sage
    """
    processing_files = get_processing_files()

    for file in processing_files:
        error = False
        trace = None

        try:
            trace, to_print = processing_dict.get(file.name)(file)
            # print("trace : ", trace.pk, trace)
            # print("to_print : ", to_print)
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
        update_cct_sage()
    except Exception as except_error:
        LOGGER_IMPORT.exception(f"Exception Générale: update_cct_sage()\n{except_error!r}")

    try:
        update_code_plan()
    except Exception as except_error:
        LOGGER_IMPORT.exception(f"Exception Générale: update_code_plan()\n{except_error!r}")


if __name__ == "__main__":
    process()
