# pylint: disable=E0401
"""
FR : Module de génération de l'entête des factures en pdf
EN : Module for generating invoices in pdf

Commentaire:

created at: 2023-04-11
created by: Paulo ALVES

modified at: 2023-04-11
modified by: Paulo ALVES
"""

from typing import AnyStr
from pathlib import Path

from django.template.loader import render_to_string
from django.conf import settings
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration

from apps.invoices.bin.conf import DOMAIN
from apps.invoices.models import SaleInvoice
from apps.centers_purchasing.models import ChildCenterPurchase


def summary_invoice_pdf(cct: AnyStr, pdf_path: Path) -> None:
    """
    Generation de la page de resumé de facture
    :param cct: Maison facturée
    :param pdf_path: Path du fichier pdf
    :return: None
    """
    sale = SaleInvoice.objects.filter(
        cct=cct, final=False, printed=False, type_x3__in=(1, 2)
    ).order_by("cct", "big_category_ranking")

    if sale:
        center_puchase = ChildCenterPurchase.objects.get(
            code=sale[0].signboard.code_signboard
        )
    else:
        center_puchase = None

    context = {
        "invoices": sale,
        "logo": str(sale[0].signboard.logo_signboard).replace("logos/", ""),
        "domain": DOMAIN,
        "center_puchase": center_puchase,
    }
    content = render_to_string("invoices/pdf_summary.html", context)
    font_config = FontConfiguration()
    html = HTML(string=content)
    html.write_pdf(pdf_path, font_config=font_config)


if __name__ == "__main__":
    cct_cct = "AF0591"
    file_path = Path(settings.SALES_INVOICES_FILES_DIR) / f"{cct_cct}_summary.pdf"
    summary_invoice_pdf(cct_cct, file_path)
