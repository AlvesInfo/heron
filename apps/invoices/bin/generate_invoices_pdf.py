# pylint: disable=E0401,C0413,R0914
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
from apps.invoices.bin.pdf_marchandises import invoice_marchandise_pdf
from apps.invoices.bin.pdf_royalties import invoice_royalties_pdf
from apps.invoices.bin.pdf_publicity import invoice_publicity_pdf
from apps.invoices.bin.pdf_prestation import invoice_prestation_pdf
from apps.invoices.bin.pdf_formation import invoice_formation_pdf
from apps.invoices.bin.pdf_staff import invoice_staff_pdf
from apps.invoices.bin.pdf_material import invoice_material_pdf
from apps.invoices.bin.pdf_various import invoice_various_pdf
from apps.invoices.models import SaleInvoice


@transaction.atomic
def invoices_pdf_generation():
    """
    Génération des pdf de factures de ventes
    :return:
    """

    generation_pdf_dict = {
        "marchandises": invoice_marchandise_pdf,
        "rfa": "",
        "redevances": invoice_royalties_pdf,
        "redevances-de-publicite": invoice_publicity_pdf,
        "formation": invoice_formation_pdf,
        "personnel": invoice_staff_pdf,
        "materiel": invoice_material_pdf,
        "prestation": invoice_prestation_pdf,
        "divers": invoice_various_pdf,
    }

    cct_sales_list = (
        SaleInvoice.objects.filter(printed=False, type_x3__in=(1, 2))
        .filter(
            cct__in=(
                "ACAS001",
                # "AF0001",
                # "AF0002",
                # "AF0004",
                # "AF0005",
                # "AF0009",
                # "AF0011",
                # "AF0012",
                # "AF0014",
                # "AF0019",
                # "AF0021",
                # "AF0103",
                # "AF0104",
                # "AF0117",
                # "AF0354",
                # "AF0404",
                # "AF0501",
                # "AF0502",
                # "AF0507",
                # "AF0597",
                # "AF0705",
                # "AF0706",
                # "ARI008",
                # "ARI010",
                # "CORNER0391",
                # "DO0001",
                # "DO0006",
                # "GA0001",
                # "GA0003",
                # "GA0103",
                # "GA0203",
                # "GF0002",
                # "GF0010",
                # "GF0707",
                # "INNO001",
                # "INNO019",
                # "MF0001",
                # "UNIS001",
                # "UNIS006",
            )
        )
        .values("cct")
        .annotate(dcount=Count("cct"))
        .values_list("cct", flat=True)
        .order_by("cct")
    )

    for cct in cct_sales_list:
        files_list = []
        file_num = get_generic_cct_num(cct)
        file_path = Path(settings.SALES_INVOICES_FILES_DIR) / f"{file_num}_summary.pdf"

        files_list.append(file_path)

        # On génère le pdf du sommaire
        summary_invoice_pdf(cct, file_path)

        sales_incoices_list = (
            SaleInvoice.objects.filter(cct=cct, printed=False)
            .values_list("cct", "uuid_identification", "big_category_slug_name", "invoice_number")
            .order_by("big_category_ranking")
        )

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
                SaleInvoice.objects.filter(invoice_number=invoice_number).update(
                    invoice_file=str(file_path.name)
                )

        if files_list:
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
            SaleInvoice.objects.filter(cct=cct, printed=False).update(
                global_invoice_file=str(file_path.name)
            )


if __name__ == "__main__":
    invoices_pdf_generation()
