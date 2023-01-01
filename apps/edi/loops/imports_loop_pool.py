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
import shutil

from psycopg2 import sql
from django.db import connection
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
from apps.edi.imports.imports_suppliers_incoices_pool import (
    bbgr_bulk,
    bbgr_statment,
    bbgr_monthly,
    bbgr_retours,
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
from apps.parameters.models import ActionInProgress


processing_dict = {
    "BBGR_BULK": bbgr_bulk,
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
    """Retourne la liste des tuples (fichier, process) à traiter"""
    separate_edi()
    files_list = []

    for directory, function in processing_dict.items():
        files_directory = Path(settings.PROCESSING_SUPPLIERS_DIR) / directory
        backup_dir = Path(settings.BACKUP_SUPPLIERS_DIR) / directory

        for file in files_directory.glob("*"):
            backup_file = backup_dir / file.name
            files_list.append((file, backup_file, function))

    return files_list


def have_files():
    """Retourne True si il y a des fichiers sinon False.
    Fonction faite pour l'affichage de la page d'import en cas de rafraichissement seulement.
    Si ce n'ast pas contrôlé le rafraichissement envoie true à in_progress,
    la page ne s'affiche jamais.
    """

    with connection.cursor() as cursor:
        sql_id_statment = sql.SQL(
            """
            select 
                "max_id"
            from (
                select 
                    max("id") as max_id
                from "heron_bi_factures_billstatement"
            )he
            where exists (
                select 1 from (
                    select 
                        max(max_id) as max_id
                    from (
                        select  
                            coalesce(max(bi_id), %(historic_id)s) as max_id 
                        from edi_ediimport ee 
                        where flow_name = 'BbgrStatment'
                        union all 
                        select 
                            coalesce(max(bi_id), %(historic_id)s) as max_id 
                        from suppliers_invoices_invoice sii 
                        join suppliers_invoices_invoicedetail sii2 
                        on sii.uuid_identification  = sii2.uuid_invoice 
                        where sii.flow_name = 'BbgrStatment'
                    ) req
                ) mx 
                where mx.max_id < he.max_id
            )
            """
        )
        cursor.execute(sql_id_statment, {"historic_id": 1947055})
        test_have_lines_statment = cursor.fetchone()

        if test_have_lines_statment:
            return True

        sql_id_monthly = sql.SQL(
            """
            select 
                "max_id"
            from (
                select 
                    max("id") as max_id
                from "heron_bi_factures_monthlydelivery"
                where "type_article" not in ('FRAIS_RETOUR', 'DECOTE')
            )he
            where exists (
                select 1 from (
                    select 
                        max(max_id) as max_id
                    from (
                        select  
                            coalesce(max(bi_id), %(historic_id)s) as max_id 
                        from edi_ediimport ee 
                        where flow_name = 'BbgrMonthly'
                        union all 
                        select 
                            coalesce(max(bi_id), %(historic_id)s) as max_id 
                        from suppliers_invoices_invoice sii 
                        join suppliers_invoices_invoicedetail sii2 
                        on sii.uuid_identification  = sii2.uuid_invoice 
                        where sii.flow_name = 'BbgrMonthly'
                    ) req
                ) mx 
                where mx.max_id < he.max_id
            )
            """
        )
        cursor.execute(sql_id_monthly, {"historic_id": 2012339})
        test_have_lines_montly = cursor.fetchone()

        if test_have_lines_montly:
            return True

        sql_id_retours = sql.SQL(
            """
            select 
                "max_id"
            from (
                select 
                    max("id") as max_id
                from "heron_bi_factures_monthlydelivery"
                where "type_article" in ('FRAIS_RETOUR', 'DECOTE')
            )he
            where exists (
                select 1 from (
                    select 
                        max(max_id) as max_id
                    from (
                        select  
                            coalesce(max(bi_id), %(historic_id)s) as max_id 
                        from edi_ediimport ee 
                        where flow_name = 'BbgrRetours'
                        union all 
                        select 
                            coalesce(max(bi_id), %(historic_id)s) as max_id 
                        from suppliers_invoices_invoice sii 
                        join suppliers_invoices_invoicedetail sii2 
                        on sii.uuid_identification  = sii2.uuid_invoice 
                        where sii.flow_name = 'BbgrRetours'
                    ) req
                ) mx 
                where mx.max_id < he.max_id
            )
            """
        )
        cursor.execute(sql_id_retours, {"historic_id": 2042093})
        test_have_lines_retours = cursor.fetchone()

        if test_have_lines_retours:
            return True

    return True if get_files() else False


def proc_files(process_object):
    """
    Intégration des factures fournisseurs présentes
    dans le répertoire de processing/suppliers_invoices_files
    """
    import time

    start_initial = time.time()

    error = False
    trace = None
    to_print = ""
    file, backup_file, function = process_object

    try:
        trace, to_print = function(file)

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
            print(trace.uuid_identification)
            trace.save()

        if file.is_file():
            shutil.move(file.resolve(), backup_file.resolve())

        # TODO : faire une fonction d'envoie de mails

    EDI_LOGGER.warning(
        to_print
        + f"Validation {file.name} in : {time.time() - start_initial} s"
        + "\n\n======================================================================="
        "======================================================================="
    )


def loop_proc(proc_files_list):
    """Lancement des process en Thread pool"""
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor() as executor:
        executor.map(proc_files, proc_files_list)

    post_processing_all()


def loop_pool_proc(proc_files_list):
    """Lancement des process en Multiprocessing pool"""
    from multiprocessing import Pool

    with Pool(8) as pool:
        pool.map(proc_files, proc_files_list)


def main():
    import time

    # Si l'action n'existe pas on la créée
    try:
        action = ActionInProgress.objects.get(action="import_edi_invoices")
        print("GET ACTION")
    except ActionInProgress.DoesNotExist:
        action = ActionInProgress(
            action="import_edi_invoices",
            comment="Executable pour l'import des fichiers edi des factures founisseurs",
        )
        action.save()
        print("EXCEPT")

    try:

        # Si l'action est déjà en cours, on ne fait rien
        if not action.in_progress:
            print("ACTION")
            # On initialise l'action comme en cours
            action.in_progress = True
            action.save()
            start_all = time.time()

            # On insert BBGR STATMENT
            bbgr_statment()
            # On insert BBGR MONTHLY
            bbgr_monthly()
            # On insert BBGR RETOURS
            bbgr_retours()

            # On boucle sur les fichiers à insérer
            proc_files_l = get_files()
            loop_proc(proc_files_l)
            print(f"All validations : {time.time() - start_all} s")
            EDI_LOGGER.warning(f"All validations : {time.time() - start_all} s")

    except:
        EDI_LOGGER.exception(f"Erreur détectée dans apps.edi.loops.imports_loop_pool.main()")

    finally:
        # On remet l'action en cours à False, après l'execution
        action.in_progress = False
        action.save()


def main_pool():
    import time

    # Si l'action n'existe pas on la créée
    try:
        action = ActionInProgress.objects.get(action="import_edi_invoices")
        print("GET ACTION")
    except ActionInProgress.DoesNotExist:
        action = ActionInProgress(
            action="import_edi_invoices",
            comment="Executable pour l'import des fichiers edi des factures founisseurs",
        )
        action.save()
        print("EXCEPT")

    # Si l'action est déjà en cours, on ne fait rien
    if not action.in_progress:
        print("ACTION")
        # On initialise l'action comme en cours
        action.in_progress = True
        action.save()

        start_all = time.time()

        proc_files_l = get_files()
        loop_pool_proc(proc_files_l)
        print(f"All validations : {time.time() - start_all} s")
        EDI_LOGGER.warning(f"All validations : {time.time() - start_all} s")

        # On remet l'action en cours à False, après l'execution
        action.in_progress = False
        action.save()


if __name__ == "__main__":
    main()
    # post_processing_all()
    # get_files()
    # separate_edi()
