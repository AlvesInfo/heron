# pylint: disable=E0401
"""
FR : Module de génération des factures de marchandises en pdf
EN : Module for generating invoices marchandises in pdf

Commentaire:

created at: 2023-04-11
created by: Paulo ALVES

modified at: 2023-04 -11
modified by: Paulo ALVES
"""
import os
import sys
import platform
import datetime
from typing import AnyStr
from pathlib import Path
from uuid import UUID

import pendulum
import pdfkit
import django

BASE_DIR = r"/"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")
django.setup()

from django.template.loader import render_to_string
from django.conf import settings
from django.db import connection
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration

from apps.invoices.models import SaleInvoice, SaleInvoiceDetail
from apps.invoices.sql_files.sql_pdf import SQL_HEADAER, SQL_RESUME_HEADER


def marchandise_header_invoice_pdf(uuid_invoice: UUID) -> None:
    """
    Génération des entêtes de factures de marchandises
    :param uuid_invoice: uuid_identification de la facture
    :return: None
    """

    with connection.cursor() as cursor:
        cursor.execute(SQL_HEADAER, {"uuid_invoice": uuid_invoice})
        header = cursor.fetchall()
        cursor.execute(SQL_RESUME_HEADER, {"uuid_invoice": uuid_invoice})
        resume = cursor.fetchone()
        invoice = SaleInvoice.objects.get(uuid_identification=uuid_invoice)
        context = {
            "invoice": invoice,
            "details": header,
            "resume": resume,
            "logo_heron": str((Path(settings.STATIC_DIR) / "logo_heron_01.png").resolve()),
            "logo_enseigne": str(Path(settings.MEDIA_URL).resolve()),
        }
        content = render_to_string("invoices/summary.html", context)
        pdf_file = Path(settings.SALES_INVOICES_FILES_DIR) / "AF0518_header_marchandise.pdf"
        font_config = FontConfiguration()
        html = HTML(string=content)
        html.write_pdf(pdf_file, font_config=font_config)


def marchandises_suppliers_invoice_pdf(invoice_number: AnyStr) -> None:
    """
    Génération des récapitulatifs par fournisseurs
    :param invoice_number: N° de facture
    :return:
    """


def marchandise_details_invoice_pdf(invoice_number: AnyStr) -> None:
    """
    Génération des pages de marchandises
    :param invoice_number: N° de facture
    :return: No
    """


def marchandise_sub_details_invoice_pdf(invoice_number: AnyStr) -> None:
    """
    Génération des pages de marchandises
    :param invoice_number: N° de facture
    :return: None
    """


if __name__ == "__main__":
    marchandise_header_invoice_pdf(
        uuid_invoice=UUID("15ff7e2c-c6f8-40e3-9e5d-24e9c98ad6a5")
    )
