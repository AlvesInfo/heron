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
import time

from psycopg2 import sql
import django
from django.db import connection, connections
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
    z_bu_refac,
)
from apps.edi.bin.bbgr_002_statment import HISTORIC_STATMENT_ID
from apps.edi.bin.bbgr_003_monthly import HISTORIC_MONTHLY_ID
from apps.edi.bin.bbgr_004_retours import HISTORIC_RETOURS_ID
from apps.edi.bin.bbgr_005_receptions import HISTORIC_RECEPTIONS_ID
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
    "SAGE_YOOZ_REFAC0": z_bu_refac,
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


def get_retours_valid():
    """Vérifie que tous les retours sont validés avant import"""
    with connections["bi_bdd"].cursor() as cursor:
        sql_valid = """
            SELECT count(*) 
            FROM "factures_monthlyretours" 
            WHERE "factures_monthlyretours"."validation" = False
        """
        cursor.execute(sql_valid)
        result = cursor.fetchone()[0]

        return not bool(result)


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

    if bool(get_files_celery()):
        return True

    return False


def get_action():
    """Récupération de l'état d'action"""

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

    return action


def celery_import_launch():
    """Main pour lancement de l'import avec Celery"""

    # Si l'action n'existe pas on la créée
    action = get_action()

    try:
        tasks_list = []

        # Si l'action est déjà en cours, on ne fait rien
        if not action.in_progress:
            print("ACTION")
            # On initialise l'action comme en cours
            action.in_progress = True
            action.save()
            start_all = time.time()

            # On boucle sur les fichiers à insérer
            proc_files_l = get_files_celery()

            for row_args in proc_files_l:
                tasks_list.append(
                    celery_app.signature("suppliers_import", kwargs={"process_objects": row_args})
                )

            result = group(*tasks_list)().get(3600)
            print("result : ", result)
            EDI_LOGGER.warning(f"result : {result!r},\nin {time.time() - start_all} s")

            result_clean = group(*[
                celery_app.signature("sql_clean_general", kwargs={"start_all": start_all})
            ])().get(3600)

            print("result_clean : ", result_clean)
            EDI_LOGGER.warning(f"result_clean : {result_clean!r},\nin {time.time() - start_all} s")

    except Exception as error:
        print("Error : ", error)
        EDI_LOGGER.exception(
            "Erreur détectée dans apps.edi.loops.imports_loop_pool.celery_import_launch()"
        )

    finally:
        # On remet l'action en cours à False, après l'execution
        action.in_progress = False
        action.save()


def import_launch_bbgr(function_name):
    """Main pour lancement de l'import"""

    # Si l'action n'existe pas on la créée
    action = get_action()

    try:
        start_all = time.time()

        # On initialise l'action comme en cours
        action.in_progress = True
        action.save()
        result = group(
            *[celery_app.signature("bbgr_bi", kwargs={"function_name": function_name})]
        )().get(3600)
        print("result : ", result)
        EDI_LOGGER.warning(f"result : {result!r},\nin {time.time() - start_all} s")

        result_clean = group(*[
            celery_app.signature("sql_clean_general", kwargs={"start_all": start_all})
        ])().get(3600)

        print("result_clean : ", result_clean)
        EDI_LOGGER.warning(f"result_clean : {result_clean!r},\nin {time.time() - start_all} s")

    except Exception as error:
        print("Error : ", error)
        EDI_LOGGER.exception(
            "Erreur détectée dans apps.edi.loops.imports_loop_pool.import_launch_bbgr()"
        )

    finally:
        # On remet l'action en cours à False, après l'execution
        action.in_progress = False
        action.save()


if __name__ == "__main__":
    # post_processing_all()
    # get_files()
    separate_edi()
