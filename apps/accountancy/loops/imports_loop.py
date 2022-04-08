# pylint: disable=
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

from apps.accountancy.loggers import IMPORT_LOGGER
from apps.core.functions.functions_setups import settings
from apps.accountancy.imports.imports_sage import (
    account_sage,
    axe_sage,
    section_sage,
    vat_regime_sage,
    vat_sage,
    vat_rat_sage,
    payement_condition,
    tab_div_sage,
    category_sage,
)

processing_dict = {
    "ZBIACCOUNT_journalier.heron": account_sage,
    "ZBIAXES_journalier.heron": axe_sage,
    "ZBICCE_journalier.heron": section_sage,
    "ZBIREG_journalier.heron": vat_regime_sage,
    "ZBIVAT_journalier.heron": vat_sage,
    "ZBIRATVAT_journalier.heron": vat_rat_sage,
    "ZBIPTE_journalier.heron": payement_condition,
    "ZBIDIV_journalier.heron": tab_div_sage,
    "ZBICATC_journalier.heron": category_sage,
    "ZBICATS_journalier.heron": category_sage,
}


def get_processing_files():
    """Récupération des fichiers Sage à intégrer, depuis le serveur Sage X3"""
    file_list = []

    for file in Path(settings.ACUITIS_EM_DIR).glob("*"):
        if file.name in processing_dict.keys():
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
            trace = processing_dict.get(file.name)(file)
            destination = Path(settings.BACKUP_SAGE_DIR) / file.name
            shutil.move(file.resolve(), destination.resolve())

        except TypeError as except_error:
            error = True
            IMPORT_LOGGER.exception(f"TypeError : {except_error!r}")

        except Exception as except_error:
            error = True
            IMPORT_LOGGER.exception(f"Exception Générale: {file.name}\n{except_error!r}")

        finally:
            if error and trace:
                trace.errors = True
                trace.comment = (
                        "Une erreur c'est produite veuillez consulter les logs\n" + trace.comment
                )
                trace.save()


if __name__ == "__main__":
    process()
