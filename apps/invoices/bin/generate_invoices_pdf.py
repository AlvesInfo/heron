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
from typing import AnyStr

import django

BASE_DIR = r"/"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")

django.setup()


from django.conf import settings
from django.db import transaction
from pdfrw import PdfReader, PdfWriter
from django_celery_results.models import TaskResult

from heron.loggers import LOGGER_INVOICES
from apps.data_flux.trace import get_trace
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


def get_invoices_in_progress():
    """Renvoi si un process d'intégration edi est en cours"""
    in_action_insertion = TaskResult.objects.filter(
        status="STARTED", task_name="invoices_insertions_launch"
    ).exists()
    in_action_pdf_invoices = TaskResult.objects.filter(
        status="STARTED", task_name="launch_generate_pdf_invoices"
    ).exists()
    in_action_email_invoices = TaskResult.objects.filter(
        status="STARTED", task_name="send_invoice_email"
    ).exists()

    return in_action_insertion, in_action_pdf_invoices, in_action_email_invoices


@transaction.atomic
def invoices_pdf_generation(cct: Maison.cct, num_file: AnyStr):
    """
    Génération des pdf de factures de ventes
    :param cct: cct de la facture pdf à générer
    :param num_file: numero du fichier full
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
    to_print = ""

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

        files_list = []
        file_num = num_file.replace("_full.pdf", "")
        file_path = Path(settings.SALES_INVOICES_FILES_DIR) / f"{file_num}_summary.pdf"

        files_list.append(file_path)

        # On génère le pdf du sommaire
        summary_invoice_pdf(cct, file_path)

        sales_invoices_list = (
            SaleInvoice.objects.filter(
                cct=cct,
                global_invoice_file=num_file,
                final=False,
                printed=False,
                type_x3__in=(1, 2),
            )
            .values_list("cct", "uuid_identification", "big_category_slug_name", "invoice_number")
            .order_by("big_category_ranking")
        )

        # On boucle sur le différent type de factures
        for sale in sales_invoices_list:
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

        # On fusionne les pdf
        writer = PdfWriter()

        # On ajoute chaque page de chaque fichier PDF à l'objet PdfWriter
        for pdf_file in files_list:
            reader = PdfReader(pdf_file)
            for page in reader.pages:
                writer.addpage(page)

        # On enregistre le fichier PDF fusionné
        file_path = Path(settings.SALES_INVOICES_FILES_DIR) / num_file
        writer.write(file_path)

        # On supprime les fichiers intermédiaires
        for file in files_list:
            file.unlink()

        trace.file_name = f"Generate pdf : {num_file}"
        to_print = f"have generate pdf : {num_file} - "

    except Exception as except_error:
        error = True
        LOGGER_INVOICES.exception(f"Exception Générale : {except_error!r}")

    finally:
        if error:
            trace.errors = True
            trace.comment = (
                trace.comment + "\n. Une erreur c'est produite veuillez consulter les logs"
            )
        else:
            SaleInvoice.objects.filter(
                cct=cct,
                global_invoice_file=num_file,
                final=False,
                printed=False,
                type_x3__in=(1, 2),
            ).update(printed=True)

        trace.save()

    return trace, to_print


if __name__ == "__main__":
    # invoices_pdf_generation("AF0564")
    invoices_pdf_generation("AF0597", "AF0021_0000001199")
