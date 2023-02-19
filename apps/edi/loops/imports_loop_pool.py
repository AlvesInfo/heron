# pylint: disable=E0401,W0703,W1203,C0413,C0303,W1201,E1101,C0415,E0611,W0511
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
import time

from psycopg2 import sql
import django
from django.db import connection
from celery import group
from heron import celery_app

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
    cosium,
    transfert_cosium,
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
from apps.edi.bin.bbgr_002_statment import HISTORIC_STATMENT_ID
from apps.edi.bin.bbgr_003_monthly import HISTORIC_MONTHLY_ID
from apps.edi.bin.bbgr_004_retours import HISTORIC_RETOURS_ID
from apps.edi.bin.bbgr_005_receptions import HISTORIC_RECEPTIONS_ID
from apps.edi.bin.edi_post_processing_pool import post_common
from apps.edi.bin.edi_post_processing_pool import post_processing_all
from apps.parameters.models import ActionInProgress


processing_dict = {
    "BBGR_BULK": bbgr_bulk,
    "COSIUM": cosium,
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
    "TRANSFERTS": transfert_cosium,
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


def get_files_celery():
    """Retourne la liste des tuples (fichier, process) à traiter par celery,
    ne pouvant serializer des fonctions ou objets python
    """
    separate_edi()
    files_list = []

    for directory, _ in processing_dict.items():
        files_directory = Path(settings.PROCESSING_SUPPLIERS_DIR) / directory
        backup_dir = Path(settings.BACKUP_SUPPLIERS_DIR) / directory

        for file in files_directory.glob("*"):
            backup_file = backup_dir / file.name
            files_list.append((str(file), str(backup_file), directory))
    return files_list


def get_have_statment():
    """Vérifie si il y a des statment à intégrer"""
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
                        from invoices_invoice sii 
                        join invoices_invoicedetail sii2 
                        on sii.uuid_identification  = sii2.uuid_invoice 
                        where sii.flow_name = 'BbgrStatment'
                    ) req
                ) mx 
                where mx.max_id < he.max_id
            )
            """
        )
        cursor.execute(sql_id_statment, {"historic_id": HISTORIC_STATMENT_ID})
        test_have_lines_statment = cursor.fetchone()

        if test_have_lines_statment:
            return True

    return False


def get_have_monthly():
    """Verification si il y a des Monthly"""

    with connection.cursor() as cursor:
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
                        from invoices_invoice sii 
                        join invoices_invoicedetail sii2 
                        on sii.uuid_identification  = sii2.uuid_invoice 
                        where sii.flow_name = 'BbgrMonthly'
                    ) req
                ) mx 
                where mx.max_id < he.max_id
            )
            """
        )
        cursor.execute(sql_id_monthly, {"historic_id": HISTORIC_MONTHLY_ID})
        test_have_lines_montly = cursor.fetchone()

        if test_have_lines_montly:
            return True

    return False


def get_have_retours():
    """Verification si il y a des Retours"""

    with connection.cursor() as cursor:
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
                        from invoices_invoice sii 
                        join invoices_invoicedetail sii2 
                        on sii.uuid_identification  = sii2.uuid_invoice 
                        where sii.flow_name = 'BbgrRetours'
                    ) req
                ) mx 
                where mx.max_id < he.max_id
            )
            """
        )
        cursor.execute(sql_id_retours, {"historic_id": HISTORIC_RETOURS_ID})
        test_have_lines_retours = cursor.fetchone()

        if test_have_lines_retours:
            return True

    return False


def get_have_receptions():
    """Verification si il y a des Réceptions"""

    with connection.cursor() as cursor:
        sql_id_receptions = sql.SQL(
            """
            select 
                "max_id"
            from (
                select 
                    max("id") as max_id
                from "heron_bi_receptions_bbgr"
            )he
            where exists (
                select 1 from (
                    select 
                        max(max_id) as max_id
                    from (
                        select  
                            coalesce(max(bi_id), %(historic_id)s) as max_id 
                        from edi_ediimport ee 
                        where flow_name = 'BbgrReceptions'
                        union all 
                        select 
                            coalesce(max(bi_id), %(historic_id)s) as max_id 
                        from invoices_invoice sii 
                        join invoices_invoicedetail sii2 
                        on sii.uuid_identification  = sii2.uuid_invoice 
                        where sii.flow_name = 'BbgrReceptions'
                    ) req
                ) mx 
                where mx.max_id < he.max_id
            )
            """
        )
        cursor.execute(sql_id_receptions, {"historic_id": HISTORIC_RECEPTIONS_ID})
        test_have_lines_receptions = cursor.fetchone()

        if test_have_lines_receptions:
            return True

    return False


def have_files():
    """Verification qu'il y a des imports à faire"""
    if get_have_statment():
        return True

    if get_have_monthly():
        return True

    if get_have_retours():
        return True

    if get_have_receptions():
        return True

    if bool(get_files()):
        return True

    return False


def proc_files(process_objects):
    """
    Intégration des factures fournisseurs présentes
    dans le répertoire de processing/suppliers_invoices_files
    """
    start_initial = time.time()

    error = False
    trace = None
    to_print = ""
    file, backup_file, function = process_objects

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
            trace.save()

        if file.is_file() and not backup_file.is_file():
            shutil.move(file.resolve(), backup_file.resolve())
        elif file.is_file():
            file.unlink()

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


def loop_pool_proc(proc_files_list):
    """Lancement des process en Multiprocessing pool"""
    from multiprocessing import Pool

    with Pool(8) as pool:
        pool.map(proc_files, proc_files_list)


def main():
    """Main pour lancement de l'import"""

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
            elements_to_insert = False

            # On insert BBGR STATMENT
            if get_have_statment():
                elements_to_insert = True
                celery_app.signature("apps.edi.tasks.bbgr_statment").delay()

            # On insert BBGR MONTHLY
            if get_have_monthly():
                elements_to_insert = True
                celery_app.signature("apps.edi.tasks.bbgr_monthly").delay()

            # On insert BBGR RETOURS
            if get_have_retours():
                elements_to_insert = True
                celery_app.signature("apps.edi.tasks.bbgr_retours").delay()

            # On insert BBGR RECEPTIONS
            if get_have_receptions():
                elements_to_insert = True
                celery_app.signature("apps.edi.tasks.bbgr_receptions").delay()

            # On boucle sur les fichiers à insérer
            proc_files_l = get_files()

            if bool(proc_files_l):
                elements_to_insert = True
                loop_proc(proc_files_l)

            if elements_to_insert:
                post_common()
                post_processing_all()

                print(f"All validations : {time.time() - start_all} s")
                EDI_LOGGER.warning(f"All validations : {time.time() - start_all} s")

            else:
                print(f"Rien à Insérer : {time.time() - start_all} s")
                EDI_LOGGER.warning(f"Rien à Insérer : {time.time() - start_all} s")

    except:
        EDI_LOGGER.exception("Erreur détectée dans apps.edi.loops.imports_loop_pool.main()")

    finally:
        # On remet l'action en cours à False, après l'execution
        action.in_progress = False
        action.save()


def celery_import_launch():
    """Main pour lancement de l'import"""

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

        tasks_list = []

        # Si l'action est déjà en cours, on ne fait rien
        if not action.in_progress:
            print("ACTION")
            # On initialise l'action comme en cours
            action.in_progress = True
            action.save()
            start_all = time.time()
            elements_to_insert = False

            # On insert BBGR STATMENT
            if get_have_statment():
                elements_to_insert = True
                tasks_list.append(celery_app.signature("apps.edi.tasks.bbgr_statment"))

            # On insert BBGR MONTHLY
            if get_have_monthly():
                elements_to_insert = True
                tasks_list.append(celery_app.signature("apps.edi.tasks.bbgr_monthly"))

            # On insert BBGR RETOURS
            if get_have_retours():
                elements_to_insert = True
                tasks_list.append(celery_app.signature("apps.edi.tasks.bbgr_retours"))

            # On insert BBGR RECEPTIONS
            if get_have_receptions():
                elements_to_insert = True
                tasks_list.append(celery_app.signature("apps.edi.tasks.bbgr_receptions"))

            # On boucle sur les fichiers à insérer
            proc_files_l = get_files_celery()

            if bool(proc_files_l):
                elements_to_insert = True

                for row_args in proc_files_l:
                    tasks_list.append(
                        celery_app.signature(
                            "suppliers_import", kwargs={"process_objects": row_args}
                        )
                    )

            if elements_to_insert:
                result = group(*tasks_list)().get(3600)
                print("result : ", result)
                EDI_LOGGER.warning(f"result : {result!r},\nin {time.time() - start_all} s")
                post_common()
                print("post_common terminé")
                EDI_LOGGER.warning("post_common terminé")
                post_processing_all()
                print("post_processing_all terminé")
                EDI_LOGGER.warning("post_processing_all terminé")

                print(f"All validations : {time.time() - start_all} s")
                EDI_LOGGER.warning(f"All validations : {time.time() - start_all} s")

            else:
                print(f"Rien à Insérer : {time.time() - start_all} s")
                EDI_LOGGER.warning(f"Rien à Insérer : {time.time() - start_all} s")

    except Exception as error:
        print("Error : ", error)
        EDI_LOGGER.exception(
            "Erreur détectée dans apps.edi.loops.imports_loop_pool.celery_import_launch()"
        )

    finally:
        # On remet l'action en cours à False, après l'execution
        action.in_progress = False
        action.save()


def main_pool():
    """main pool"""
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
