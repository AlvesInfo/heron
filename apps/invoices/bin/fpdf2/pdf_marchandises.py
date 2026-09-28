# pylint: disable=E0401,C0413
"""
FR : Module de génération des factures de marchandises en pdf (version fpdf2)
EN : Module for generating invoices marchandises in pdf (fpdf2 version)

created at: 2024-02-10
created by: Paulo ALVES
"""
from pathlib import Path
from uuid import UUID
from typing import AnyStr

from django.conf import settings
from pdfrw import PdfReader, PdfWriter

from apps.invoices.bin.fpdf2.pdf_marchandises_header import marchandise_header_invoice_pdf
from apps.invoices.bin.fpdf2.pdf_marchandises_suppliers import marchandise_suppliers_invoice_pdf
from apps.invoices.bin.fpdf2.pdf_marchandises_details import marchandise_details_invoice_pdf
from apps.invoices.bin.fpdf2.pdf_marchandises_sub_details import marchandise_sub_details_invoice_pdf
from apps.invoices.models import SaleInvoice


def invoice_marchandise_pdf(uuid_invoice: UUID, pdf_path: AnyStr) -> None:
    """
    Génération complète de la facture marchandises (4 parties fusionnées)
    :param uuid_invoice: uuid_identification de la facture
    :param pdf_path: Path du fichier pdf final
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
        pdf_path_name = Path(str(pdf_path)[:-4] + f"_{name}.pdf")
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
    uuid_invoice_to_pdf = UUID("8b4ac234-e03e-4ac6-bf9e-491a40cab635")
    sale = SaleInvoice.objects.get(uuid_identification=uuid_invoice_to_pdf)

    header_path = Path(settings.SALES_INVOICES_FILES_DIR) / f"{sale.cct}_header_marchandise.pdf"
    marchandise_header_invoice_pdf(uuid_invoice=uuid_invoice_to_pdf, pdf_path=header_path)

    supplier_path = (
        Path(settings.SALES_INVOICES_FILES_DIR) / f"{sale.cct}_supplier_marchandise.pdf"
    )
    marchandise_suppliers_invoice_pdf(uuid_invoice=uuid_invoice_to_pdf, pdf_path=supplier_path)

    details_path = (
        Path(settings.SALES_INVOICES_FILES_DIR) / f"{sale.cct}_details_marchandise.pdf"
    )
    marchandise_details_invoice_pdf(uuid_invoice=uuid_invoice_to_pdf, pdf_path=details_path)

    sub_path = Path(settings.SALES_INVOICES_FILES_DIR) / f"{sale.cct}_sub_marchandise.pdf"
    marchandise_sub_details_invoice_pdf(uuid_invoice=uuid_invoice_to_pdf, pdf_path=sub_path)

    sub_path = (
        Path(settings.SALES_INVOICES_FILES_DIR) / f"{sale.cct}_{sale.invoice_number}.pdf"
    )
    invoice_marchandise_pdf(uuid_invoice=uuid_invoice_to_pdf, pdf_path=sub_path)