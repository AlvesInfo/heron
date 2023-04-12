# pylint: disable=E0401
"""
FR : Module de génération des factures en pdf
EN : Module for generating invoices in pdf

Commentaire:

created at: 2023-04-11
created by: Paulo ALVES

modified at: 2023-04 -11
modified by: Paulo ALVES
"""
import os
import sys
import platform
from typing import AnyStr
from pathlib import Path

import django

BASE_DIR = r"/"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")
django.setup()

from django.template.loader import render_to_string
from django.conf import settings
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration

from apps.invoices.models import SaleInvoice


def summary_invoice_pdf(cct: AnyStr) -> None:
    """
    Generation de la page de resumé de facture
    :param cct: Maison facturée
    :return: None
    """
    context = {
        "invoices": SaleInvoice.objects.filter(cct=cct),
        "logo_heron": str((Path(settings.STATIC_DIR) / "logo_heron_01.png").resolve()),
        "logo_enseigne": str(Path(settings.MEDIA_URL).resolve()),
    }
    content = render_to_string("invoices/summary.html", context)
    pdf_file = Path(settings.SALES_INVOICES_FILES_DIR) / f"{cct}cct.pdf"
    font_config = FontConfiguration()
    html = HTML(string=content)
    html.write_pdf(pdf_file, font_config=font_config)


if __name__ == '__main__':
    cct_cct = "AF0518"
    summary_invoice_pdf(cct_cct)
