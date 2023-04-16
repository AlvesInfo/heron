# pylint: disable=E0401
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

import django

BASE_DIR = r"/"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")

django.setup()

from django.db.models import Count
from django.conf import settings
from django.db import transaction
from pdfrw import PdfReader, PdfWriter

from apps.parameters.bin.generic_nums import get_generic_cct_num
from apps.invoices.bin.pdf_sumary import summary_invoice_pdf
from apps.invoices.bin.pdf_marchandises import (
    marchandise_header_invoice_pdf,
    marchandises_suppliers_invoice_pdf,
    marchandise_details_invoice_pdf,
    marchandise_sub_details_invoice_pdf,
)
from apps.invoices.bin.pdf_royalties import royalties_invoice_pdf
from apps.invoices.models import SaleInvoice


@transaction.atomic
def invoices_pdf_generation():
    """
    Génération des pdf de factures de ventes
    :return:
    """

    generation_pdf_dict = {
        "marchandises": [
            marchandise_header_invoice_pdf,
            marchandises_suppliers_invoice_pdf,
            marchandise_details_invoice_pdf,
            marchandise_sub_details_invoice_pdf,
        ],
        "rfa": [],
        "redevances": [royalties_invoice_pdf],
        "redevances-de-publicite": [],
        "formation": [],
        "personnel": [],
        "materiel": [],
        "divers": [],
        "prestation": [],
    }

    cct_filter = ["AF0001", "AF0514", "AF0551", "GA0001", "ACAL001", "AF0351", "AF0549", "AF0014"]

    cct_sales_list = (
        SaleInvoice.objects.filter(printed=False)
        .values("cct")
        .annotate(dcount=Count("cct"))
        .values_list("cct", flat=True)
    )

    for cct in cct_sales_list:
        if cct in cct_filter:
            files_list = []
            file_num = get_generic_cct_num(cct)
            file_path = Path(settings.SALES_INVOICES_FILES_DIR) / f"{file_num}_summary.pdf"
            print(f"{file_num}_summary.pdf")
            files_list.append(file_path)

            # On génère le pdf du sommaire
            summary_invoice_pdf(cct, file_path)

            sales_incoices_list = SaleInvoice.objects.filter(cct=cct, printed=False).values_list(
                "cct", "uuid_identification", "big_category_slug_name"
            )

            for sale in sales_incoices_list:
                cct_sale, uuid_identification, big_category_slug_name = sale

                for generation_pdf in generation_pdf_dict.get(big_category_slug_name, []):
                    name = generation_pdf.__name__.split("_")[1]
                    file_path = Path(settings.SALES_INVOICES_FILES_DIR) / f"{file_num}_{name}.pdf"
                    files_list.append(file_path)
                    print(f"{file_num}_{name}.pdf")
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
            file_path = Path(settings.SALES_INVOICES_FILES_DIR) / f"{file_num}_full.pdf"
            print(f"{file_num}_full.pdf")
            writer.write(file_path)
            SaleInvoice.objects.filter(cct=cct, printed=False).update(
                global_invoice_file=str(file_path)
            )


if __name__ == "__main__":
    invoices_pdf_generation()
