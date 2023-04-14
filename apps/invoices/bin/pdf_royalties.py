# pylint: disable=E0401
"""
FR : Module de génération des factures de Royalties en pdf
EN : Module for generating invoices Royalties in pdf

Commentaire:

created at: 2023-04-14
created by: Paulo ALVES

modified at: 2023-04-14
modified by: Paulo ALVES
"""
import os
import sys
import platform
from pathlib import Path

import django
from django.template.loader import render_to_string
from django.conf import settings
from django.db import connection
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration

BASE_DIR = r"/"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")
django.setup()

from apps.invoices.models import SaleInvoice

DOMAIN = "http://10.185.51.9" if BASE_DIR == "/home/paulo/heron" else "http://127.0.0.1:8000"


def royalties_invoice_pdf(uuid_invoice: UUID, pdf_path: Path) -> None:
    """
    Generation de la facture de Royalties
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
        content = render_to_string("invoices/marchandises_header.html", context)
        font_config = FontConfiguration()
        html = HTML(string=content)
        html.write_pdf(pdf_path, font_config=font_config)


if __name__ == '__main__':
    cct_cct = "AF0518"
    file_path = Path(settings.SALES_INVOICES_FILES_DIR) / f"{cct_cct}_summary.pdf"
    summary_invoice_pdf(cct_cct, file_path)