# pylint: disable=E0401
"""
FR : Module de génération des factures de Materiel en pdf
EN : Module for generating invoices Material in pdf

Commentaire:

created at: 2023-04-20
created by: Paulo ALVES

modified at: 2023-04-20
modified by: Paulo ALVES
"""
from uuid import UUID
from pathlib import Path

from django.template.loader import render_to_string
from django.conf import settings
from django.db import connection
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration

from apps.invoices.bin.conf import DOMAIN
from apps.invoices.models import SaleInvoice
from apps.invoices.sql_files.sql_material import SQL_HEADER, SQL_RESUME_HEADER
from heron.loggers import LOGGER_INVOICES


def invoice_material_pdf(uuid_invoice: UUID, pdf_path: Path) -> None:
    """
    Generation de la facture de materiel
    :param uuid_invoice: uuid_identification de la facture
    :param pdf_path: Path du fichier pdf
    :return: None
    """

    with connection.cursor() as cursor:
        # On fait un filter et non pas un get, pour pouvoir utiliser les éléments
        # tels que "general_footer_invoices.htmml" et "general_style_invoices"
        invoices = SaleInvoice.objects.filter(uuid_identification=uuid_invoice)

        # HEADER
        # print(cursor.mogrify(SQL_HEADER, {"uuid_invoice": uuid_invoice}).decode())
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
        content = render_to_string("invoices/pdf_material.html", context)
        font_config = FontConfiguration()
        html = HTML(string=content)
        html.write_pdf(pdf_path, font_config=font_config)


if __name__ == "__main__":
    uuid_invoice_to_pdf = UUID("efc5be7e-f6ea-4f69-a2fc-babb01a3fe3a")
    sale = SaleInvoice.objects.get(uuid_identification=uuid_invoice_to_pdf)

    material_path = Path(settings.SALES_INVOICES_FILES_DIR) / f"{sale.cct}_material.pdf"
    invoice_material_pdf(uuid_invoice=uuid_invoice_to_pdf, pdf_path=material_path)
