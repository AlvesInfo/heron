"""FR : Module de génération des factures de Publicité en pdf.

EN : Module for generating invoices Publicity in pdf.

Commentaire:

created at: 2023-04-16
created by: Paulo ALVES

modified at: 2023-04-16
modified by: Paulo ALVES
"""

from pathlib import Path
from uuid import UUID

from django.conf import settings
from django.db import connection
from django.template.loader import render_to_string
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration

from apps.core.bin.typing_helpers import required
from apps.invoices.models import SaleInvoice
from apps.invoices.sql_files.sql_publicity import SQL_HEADER, SQL_RESUME_HEADER


def invoice_publicity_pdf(uuid_invoice: UUID, pdf_path: Path) -> None:
    """Generation de la facture de Publicité.

    :param uuid_invoice: uuid_identification de la facture
    :param pdf_path: Path du fichier pdf
    :return: None.
    """
    with connection.cursor() as cursor:
        # On fait un filter et non pas un get, pour pouvoir utiliser les éléments
        # tels que "general_footer_invoices.htmml" et "general_style_invoices"
        invoices = SaleInvoice.objects.filter(uuid_identification=uuid_invoice)

        # HEADER
        cursor.execute(SQL_HEADER, {"uuid_invoice": uuid_invoice})
        columns_header = [col[0] for col in cursor.description]
        headers = [dict(zip(columns_header, row, strict=False)) for row in cursor.fetchall()]

        # RESUME HEADER
        cursor.execute(SQL_RESUME_HEADER, {"uuid_invoice": uuid_invoice})
        columns_resume = [col[0] for col in cursor.description]
        resume = dict(zip(columns_resume, cursor.fetchall()[0], strict=False))

        # LANCEMENT
        context = {
            "invoices": invoices,
            "headers": headers,
            "resume": resume,
            "domain": settings.PDF_STATIC_DOMAIN,
            "logo": str(required(invoices[0].signboard, "enseigne").logo_signboard).replace(
                "logos/", ""
            ),
        }
        content = render_to_string("invoices/pdf_publicity.html", context)
        font_config = FontConfiguration()
        html = HTML(string=content)
        html.write_pdf(pdf_path, font_config=font_config)


if __name__ == "__main__":
    uuid_invoice_to_pdf = UUID("bbdd8a4a-48d3-4a81-bada-ad9948688ac2")
    sale = SaleInvoice.objects.get(uuid_identification=uuid_invoice_to_pdf)

    publicity_path = Path(settings.SALES_INVOICES_FILES_DIR) / f"{sale.cct}_publicity.pdf"
    invoice_publicity_pdf(uuid_invoice=uuid_invoice_to_pdf, pdf_path=publicity_path)
