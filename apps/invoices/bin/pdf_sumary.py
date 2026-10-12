"""FR : Module de génération de l'entête des factures en pdf.

EN : Module for generating invoices in pdf.

Commentaire:

created at: 2023-04-11
created by: Paulo ALVES

modified at: 2023-04-11
modified by: Paulo ALVES
"""

from pathlib import Path

from django.conf import settings
from django.template.loader import render_to_string
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration

from apps.centers_purchasing.models import ChildCenterPurchase
from apps.invoices.models import SaleInvoice


def summary_invoice_pdf(cct: str, pdf_path: Path) -> None:
    """Generation de la page de resumé de facture.

    :param cct: Maison facturée
    :param pdf_path: Path du fichier pdf
    :return: None.
    """
    sale = SaleInvoice.objects.filter(
        cct=cct, final=False, printed=False, type_x3__in=(1, 2)
    ).order_by("cct", "big_category_ranking")

    first_sale = sale.first()
    # Sans facture à imprimer (ou sans centrale connue) la page est produite sans ces éléments,
    # au lieu de lever IndexError / DoesNotExist
    center_puchase = (
        ChildCenterPurchase.objects.filter(code=first_sale.signboard.code_signboard).first()
        if first_sale
        else None
    )

    context = {
        "invoices": sale,
        "logo": str(first_sale.signboard.logo_signboard).replace("logos/", "")
        if first_sale
        else "",
        "domain": settings.PDF_STATIC_DOMAIN,
        "center_puchase": center_puchase,
    }
    content = render_to_string("invoices/pdf_summary.html", context)
    font_config = FontConfiguration()
    html = HTML(string=content)
    html.write_pdf(pdf_path, font_config=font_config)


if __name__ == "__main__":
    cct_cct = "GAUDF"
    file_path = Path(settings.SALES_INVOICES_FILES_DIR) / "LAB0001_000000045014_full.pdf"
    summary_invoice_pdf(cct_cct, file_path)
