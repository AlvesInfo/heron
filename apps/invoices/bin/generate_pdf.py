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

import pendulum
import pdfkit
import django

BASE_DIR = r"/"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")
django.setup()

from django.shortcuts import render
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.shortcuts import redirect, HttpResponse
from django.conf import settings
from weasyprint import HTML, CSS
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
    }
    content = render_to_string("invoices/marchandises_summary.html", context)

    summary_css = Path(settings.BASE_DIR) / "apps/invoices/css_invoices/marchandises_summary.css"

    print(summary_css.open("r").read())
    pdf_file = Path(settings.SALES_INVOICES_FILES_DIR) / f"{cct}cct.pdf"

    font_config = FontConfiguration()
    html = HTML(string=content)
    css = CSS(string=summary_css.open("r").read(), font_config=font_config)
    html.write_pdf(pdf_file)


    # invoice_html.unlink()


if __name__ == '__main__':
    cct_cct = "AF0104"
    summary_invoice_pdf(cct_cct)
