# pylint: disable=E0401,C0413
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
from pathlib import Path
from uuid import UUID
from typing import AnyStr

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
from pdfrw import PdfReader, PdfWriter

from apps.invoices.models import SaleInvoice, EnteteDetails
from apps.invoices.sql_files.sql_marchandises import (
    SQL_HEADER,
    SQL_RESUME_HEADER,
    SQL_RESUME_SUPPLIER,
    SQL_DETAILS,
    SQL_SUB_DETAILS,
)

DOMAIN = "http://10.9.2.109" if BASE_DIR == "/home/paulo/heron" else "http://127.0.0.1:8000"


def marchandise_header_invoice_pdf(uuid_invoice: UUID, pdf_path: Path) -> AnyStr:
    """
    Génération des entêtes de factures de marchandises
    :param uuid_invoice: uuid_identification de la facture
    :param pdf_path: Path du fichier pdf
    :return: None
    """

    with connection.cursor() as cursor:
        # On fait un filter et non pas un get, pour pouvoir utiliser les éléments
        # tels que "general_footer_invoices.htmml" et "general_style_invoices"
        invoices = SaleInvoice.objects.filter(uuid_identification=uuid_invoice)

        # HEADER
        cursor.execute(SQL_HEADER, {"uuid_invoice": uuid_invoice})
        columns_header = [col[0] for col in cursor.description]
        headers = [dict(zip(columns_header, row)) for row in cursor.fetchall()]

        # RESUME HEADER
        cursor.execute(SQL_RESUME_HEADER, {"uuid_invoice": uuid_invoice})
        columns_resume = [col[0] for col in cursor.description]
        resume = [dict(zip(columns_resume, row)) for row in cursor.fetchall()][0]

        # LANCEMENT
        context = {
            "invoices": invoices,
            "headers": headers,
            "resume": resume,
            "domain": DOMAIN,
            "logo": str(invoices[0].signboard.logo_signboard).replace("logos/", ""),
        }
        content = render_to_string("invoices/pdf_marchandises_header.html", context)
        font_config = FontConfiguration()
        html = HTML(string=content)
        html.write_pdf(pdf_path, font_config=font_config)


def marchandise_suppliers_invoice_pdf(uuid_invoice: UUID, pdf_path: AnyStr) -> AnyStr:
    """
    Génération des récapitulatifs par fournisseurs
    :param uuid_invoice: uuid_identification de la facture
    :param pdf_path: Path du fichier pdf
    :return: None
    """

    with connection.cursor() as cursor:
        # On fait un filter et non pas un get, pour pouvoir utiliser les éléments
        # tels que "general_footer_invoices.htmml" et "general_style_invoices"
        invoices = SaleInvoice.objects.filter(uuid_identification=uuid_invoice)

        # RESUME BY SUPPLIERS
        cursor.execute(SQL_RESUME_SUPPLIER, {"uuid_invoice": uuid_invoice})
        columns_uppliers = [col[0] for col in cursor.description]
        suppliers = [dict(zip(columns_uppliers, row)) for row in cursor.fetchall()]

        context = {
            "invoices": invoices,
            "suppliers": suppliers,
            "domain": DOMAIN,
            "logo": str(invoices[0].signboard.logo_signboard).replace("logos/", ""),
        }
        content = render_to_string("invoices/pdf_marchandises_suppliers.html", context)
        font_config = FontConfiguration()
        html = HTML(string=content)
        html.write_pdf(pdf_path, font_config=font_config)


def marchandise_details_invoice_pdf(uuid_invoice: UUID, pdf_path: AnyStr) -> AnyStr:
    """
    Génération des pages Détails par fournisseurs
    :param uuid_invoice: uuid_identification de la facture
    :param pdf_path: Path du fichier pdf
    :return: None
    """

    with connection.cursor() as cursor:
        # On fait un filter et non pas un get, pour pouvoir utiliser les éléments
        # tels que "general_footer_invoices.htmml" et "general_style_invoices"
        invoices = SaleInvoice.objects.filter(uuid_identification=uuid_invoice)

        # DETAILS
        cursor.execute(SQL_DETAILS, {"uuid_invoice": uuid_invoice})
        columns_details = [col[0] for col in cursor.description]
        suppliers = [dict(zip(columns_details, row)) for row in cursor.fetchall()]

        context = {
            "invoices": invoices,
            "entetes": EnteteDetails.objects.all().values("column_name"),
            "suppliers": suppliers,
            "domain": DOMAIN,
            "logo": str(invoices[0].signboard.logo_signboard).replace("logos/", ""),
        }
        content = render_to_string("invoices/pdf_marchandises_details.html", context)
        font_config = FontConfiguration()
        html = HTML(string=content)
        html.write_pdf(pdf_path, font_config=font_config)


def marchandise_sub_details_invoice_pdf(uuid_invoice: UUID, pdf_path: AnyStr) -> AnyStr:
    """
    Génération des pages de marchandises
    :param uuid_invoice: uuid_identification de la facture
    :param pdf_path: Path du fichier pdf
    :return: None
    """

    with connection.cursor() as cursor:
        # On fait un filter et non pas un get, pour pouvoir utiliser les éléments
        # tels que "general_footer_invoices.htmml" et "general_style_invoices"
        invoices = SaleInvoice.objects.filter(uuid_identification=uuid_invoice)

        # DETAILS
        cursor.execute(SQL_SUB_DETAILS, {"uuid_invoice": uuid_invoice})
        columns_sub_details = [col[0] for col in cursor.description]
        sub_details = [dict(zip(columns_sub_details, row)) for row in cursor.fetchall()]

        context = {
            "invoices": invoices,
            "sub_details": sub_details,
            "domain": DOMAIN,
            "logo": str(invoices[0].signboard.logo_signboard).replace("logos/", ""),
        }
        content = render_to_string("invoices/pdf_marchandises_sub_details.html", context)
        font_config = FontConfiguration()
        html = HTML(string=content)
        html.write_pdf(pdf_path, font_config=font_config)


def invoice_marchandise_pdf(uuid_invoice: UUID, pdf_path: AnyStr) -> None:
    """
    Génération des pages de marchandises
    :param uuid_invoice: uuid_identification de la facture
    :param pdf_path: Path du fichier pdf
    :return: None
    """
    marchandise_dict = {
        "header": marchandise_header_invoice_pdf,
        "suppliers": marchandise_suppliers_invoice_pdf,
        "details": marchandise_details_invoice_pdf,
        "sub_details": marchandise_sub_details_invoice_pdf,
    }
    files_list = []

    for name, generation in marchandise_dict.items():
        pdf_path_name = Path(str(pdf_path)[:-4]+f"_{name}.pdf")
        generation(uuid_invoice=uuid_invoice, pdf_path=pdf_path_name)
        files_list.append(pdf_path_name)

    # On fusionne les pdf
    writer = PdfWriter()

    # On ajoute chaque page de chaque fichier PDF à l'objet PdfWriter
    for pdf_file in files_list:
        reader = PdfReader(pdf_file)
        for page in reader.pages:
            writer.addpage(page)

    # On enregistre le fichier PDF fusionné
    writer.write(pdf_path)

    for file in files_list:
        if file.is_file():
            file.unlink()


if __name__ == "__main__":
    uuid_invoice_to_pdf = UUID("90593cd2-c984-4e6f-a3da-812002495941")
    sale = SaleInvoice.objects.get(uuid_identification=uuid_invoice_to_pdf)

    # header_path = Path(settings.SALES_INVOICES_FILES_DIR) / f"{sale.cct}_header_marchandise.pdf"
    # marchandise_header_invoice_pdf(uuid_invoice=uuid_invoice_to_pdf, pdf_path=header_path)

    # supplier_path = Path(settings.SALES_INVOICES_FILES_DIR) / f"{sale.cct}_supplier_marchandise.pdf"
    # marchandise_suppliers_invoice_pdf(uuid_invoice=uuid_invoice_to_pdf, pdf_path=supplier_path)

    # details_path = Path(settings.SALES_INVOICES_FILES_DIR) / f"{sale.cct}_details_marchandise.pdf"
    # marchandise_details_invoice_pdf(uuid_invoice=uuid_invoice_to_pdf, pdf_path=details_path)

    # sub_path = Path(settings.SALES_INVOICES_FILES_DIR) / f"{sale.cct}_sub_marchandise.pdf"
    # marchandise_sub_details_invoice_pdf(uuid_invoice=uuid_invoice_to_pdf, pdf_path=sub_path)

    sub_path = Path(settings.SALES_INVOICES_FILES_DIR) / f"{sale.cct}_{sale.invoice_number}.pdf"
    invoice_marchandise_pdf(uuid_invoice=uuid_invoice_to_pdf, pdf_path=sub_path)
