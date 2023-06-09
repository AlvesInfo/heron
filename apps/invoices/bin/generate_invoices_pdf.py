# pylint: disable=E0401,C0413,R0914,W0718,W1203
"""
FR : Module de génération des factures en pdf
EN : Module for generating invoice headers in pdf

Commentaire:

created at: 2023-04-13
created by: Paulo ALVES

modified at: 2023-04-13
modified by: Paulo ALVES
"""
import os
import sys
import platform
from pathlib import Path
import time

import django

BASE_DIR = r"/"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")

django.setup()

from django.db.models import Count
from django.conf import settings
from django.db import connection
from pdfrw import PdfReader, PdfWriter
from celery import group
from django_celery_results.models import TaskResult

from heron.loggers import LOGGER_INVOICES
from heron import celery_app
from apps.data_flux.trace import get_trace
from apps.parameters.bin.generic_nums import get_generic_cct_num
from apps.parameters.bin.core import get_action
from apps.invoices.bin.pdf_sumary import summary_invoice_pdf
from apps.invoices.bin.pdf_marchandises import invoice_marchandise_pdf
from apps.invoices.bin.pdf_rfa import rfa_invoice_pdf
from apps.invoices.bin.pdf_royalties import invoice_royalties_pdf
from apps.invoices.bin.pdf_publicity import invoice_publicity_pdf
from apps.invoices.bin.pdf_prestation import invoice_prestation_pdf
from apps.invoices.bin.pdf_formation import invoice_formation_pdf
from apps.invoices.bin.pdf_staff import invoice_staff_pdf
from apps.invoices.bin.pdf_material import invoice_material_pdf
from apps.invoices.bin.pdf_various import invoice_various_pdf
from apps.invoices.models import SaleInvoice
from apps.centers_clients.models import Maison
from apps.parameters.models import ActionInProgress


def get_invoices_in_progress():
    """Renvoi si un process d'intégration edi est en cours"""
    insertion = False
    pdf_invoices = False

    try:
        in_action_object = ActionInProgress.objects.get(action="generate_invoices")
        in_action = in_action_object.in_progress

        # On contrôle si une tâche est réellement en cours pour éviter les faux positifs
        if in_action:
            insertion = TaskResult.objects.filter(
                task_name="apps.invoices.tasks.invoices_insertions"
            ).exclude(status__in=["SUCCESS", "FAILURE"])

            pdf_invoices = TaskResult.objects.filter(
                task_name="apps.invoices.tasks.generate_pdf_invoices"
            ).exclude(status__in=["SUCCESS", "FAILURE"])

            if not insertion and not pdf_invoices:
                in_action_object.in_progress = False
                in_action_object.save()

    except ActionInProgress.DoesNotExist:
        pass

    return insertion, pdf_invoices


def invoices_pdf_generation(cct: Maison.cct):
    """
    Génération des pdf de factures de ventes
    :param cct: cct de la facture pdf à générer
    :return:
    """
    error = False
    trace = get_trace(
        trace_name="Generate pdf invoices",
        file_name="Generate pdf",
        application_name="invoices_pdf_generation",
        flow_name="pdf_invoices",
        comment="",
    )
    files_list = []
    file_num = get_generic_cct_num(cct)

    try:
        generation_pdf_dict = {
            "marchandises": invoice_marchandise_pdf,
            "rfa": rfa_invoice_pdf,
            "redevances": invoice_royalties_pdf,
            "redevances-de-publicite": invoice_publicity_pdf,
            "formation": invoice_formation_pdf,
            "personnel": invoice_staff_pdf,
            "materiel": invoice_material_pdf,
            "prestation": invoice_prestation_pdf,
            "divers": invoice_various_pdf,
        }
        file_path = Path(settings.SALES_INVOICES_FILES_DIR) / f"{file_num}_summary.pdf"

        files_list.append(file_path)

        # On génère le pdf du sommaire
        summary_invoice_pdf(cct, file_path)

        # sales_incoices_list = (
        #     SaleInvoice.objects.filter(cct=cct, printed=False)
        #     .values_list("cct", "uuid_identification", "big_category_slug_name", "invoice_number")
        #     .order_by("big_category_ranking")
        # )
        with connection.cursor() as cursor:
            sql_invoices_list = """
            SELECT 
              "ee"."cct", 
              "ee"."uuid_identification", 
              "ee"."big_category_slug_name", 
              "ee"."invoice_number" 
            FROM 
              "invoices_saleinvoice" "ee"
            WHERE "ee"."cct" = AF0514 AND NOT "ee"."printed" 
            ORDER BY "ee"."big_category_ranking" ASC
            """
            cursor.exececute(sql_invoices_list)
            sales_incoices_list = cursor.fetchall()

        # On boucle sur le différent type de factures
        for sale in sales_incoices_list:
            cct_name, uuid_identification, big_category_slug_name, invoice_number = sale

            generation_pdf = generation_pdf_dict.get(big_category_slug_name)

            if generation_pdf:
                file_path = (
                    Path(settings.SALES_INVOICES_FILES_DIR)
                    / f"{cct_name}_{big_category_slug_name}_{invoice_number}.pdf"
                )
                files_list.append(file_path)

                # On génère le pdf des factures
                generation_pdf(uuid_identification, file_path)

                # On pose le numéro de facture dans la table des ventes
                # SaleInvoice.objects.filter(invoice_number=invoice_number).update(
                #     invoice_file=str(file_path.name)
                # )
                with connection.cursor() as cursor:
                    sql_update_file = """
                    update "invoices_saleinvoice"
                    set "invoice_file" = %(file_name)s
                    where "invoice_number" = %(invoice_number)s
                    """
                    cursor.exececute(
                        sql_update_file,
                        {"invoice_number": invoice_number, "file_name": str(file_path.name)},
                    )

        # On fusionne les pdf
        writer = PdfWriter()

        # On ajoute chaque page de chaque fichier PDF à l'objet PdfWriter
        for pdf_file in files_list:
            reader = PdfReader(pdf_file)
            for page in reader.pages:
                writer.addpage(page)

        # On enregistre le fichier PDF fusionné
        file_path = Path(settings.SALES_INVOICES_FILES_DIR) / f"{file_num}_full.pdf"
        print(f"{file_num}_full.pdf")
        writer.write(file_path)
        # On pose le numéro du récap de facturation dans la table des ventes
        # SaleInvoice.objects.filter(cct=cct, printed=False).update(
        #     global_invoice_file=str(file_path.name)
        # )
        with connection.cursor() as cursor:
            sql_update_full = """
            update "invoices_saleinvoice"
            set "global_invoice_file" = %(file_name)s
            where "cct" = %(cct)s and not "printed"
            """
            cursor.exececute(
                sql_update_full,
                {"cct": cct, "file_name": str(file_path.name)},
            )
        trace.file_name = f"Generate pdf : {file_num}_full.pdf"

    except Exception as except_error:
        error = True
        LOGGER_INVOICES.exception(f"Exception Générale : {except_error!r}")

    finally:
        if error:
            trace.errors = True
            trace.comment = (
                trace.comment + "\n. Une erreur c'est produite veuillez consulter les logs"
            )

        trace.save()

    to_print = f"Generate pdf: {file_num}_full.pdf\n"

    return trace, to_print


def celery_pdf_launch(user_pk: int):
    """
    Main pour lancement de la génération des pdf avec Celery
    :param user_pk: uuid de l'utilisateur qui a lancé le process
    """

    active_action = None
    action = True

    try:
        tasks_list = []

        while action:
            active_action = get_action(action="generate_invoices")

            if not active_action.in_progress:
                action = False

        print("ACTION")
        # On initialise l'action comme en cours
        active_action.in_progress = True
        active_action.save()
        start_all = time.time()

        # On boucle sur les factures des cct pour générer les pdf
        cct_sales_list = (
            # SaleInvoice.objects.filter(final=False, printed=False, type_x3__in=(1, 2))
            SaleInvoice.objects.filter(type_x3__in=(1, 2))
            .values("cct")
            .annotate(dcount=Count("cct"))
            .values_list("cct", flat=True)
            .order_by("cct")[:10]
        )
        cct_list = [cct for cct in cct_sales_list]

        from multiprocessing import Pool

        with Pool(8) as pool:
            pool.map(invoices_pdf_generation, cct_list)

        # for cct in cct_sales_list:
        #     tasks_list.append(
        #         celery_app.signature(
        #             "generate_pdf_invoices", kwargs={"cct": cct, "user_pk": user_pk}
        #         )
        #     )
        # print(tasks_list)
        # result = group(*tasks_list)().get(7200)
        # print("result : ", result)
        # LOGGER_INVOICES.warning(f"result : {result!r},\nin {time.time() - start_all} s")
        LOGGER_INVOICES.warning(f"result in {time.time() - start_all} s")

    except Exception as error:
        print("Error : ", error)
        LOGGER_INVOICES.exception(
            "Erreur détectée dans apps.invoices.bin.generate_invoices_pdf.celery_pdf_launch()"
        )

    finally:
        # On remet l'action en cours à False, après l'execution
        active_action.in_progress = False
        active_action.save()
