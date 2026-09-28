# pylint: disable=E0401,C0413
"""
FR : Module de generation du recapitulatif fournisseurs en pdf (version fpdf2)
EN : Module for generating supplier summary in pdf (fpdf2 version)
created at: 2024-02-10
created by: Paulo ALVES
"""
from pathlib import Path
from uuid import UUID

from django.conf import settings
from django.db import connection

from apps.invoices.models import SaleInvoice
from apps.invoices.sql_files.sql_marchandises import SQL_RESUME_SUPPLIER
from apps.invoices.bin.conf import DOMAIN
from apps.invoices.bin.fpdf2.pdf_base import HeronBasePDF
from apps.invoices.bin.fpdf2.pdf_styles import (
    COLOR_BLACK,
    COLOR_WHITE,
    COLOR_GRAY_BORDER,
    MARGIN_PORTRAIT,
    FONT_SIZE_DEFAULT,
    LINE_HEIGHT_HEADER,
    LINE_HEIGHT_ROW,
    LINE_HEIGHT_FOOTER,
)


def marchandise_suppliers_invoice_pdf(uuid_invoice: UUID, pdf_path: Path) -> None:
    """
    Generation du recapitulatif par fournisseurs en PDF via fpdf2.
    Reproduit le template pdf_marchandises_suppliers.html.

    :param uuid_invoice: uuid_identification de la facture
    :param pdf_path: Path du fichier pdf de sortie
    :return: None
    """
    with connection.cursor() as cursor:
        # On fait un filter et non pas un get, pour pouvoir utiliser les elements
        # tels que "general_footer_invoices.html" et "general_style_invoices"
        invoices = SaleInvoice.objects.filter(uuid_identification=uuid_invoice)

        # RESUME BY SUPPLIERS
        cursor.execute(SQL_RESUME_SUPPLIER, {"uuid_invoice": uuid_invoice})
        columns_suppliers = [col[0] for col in cursor.description]
        suppliers = [dict(zip(columns_suppliers, row)) for row in cursor.fetchall()]

    invoice = invoices[0]

    # --- Chemins des logos ---
    logo_heron = Path(settings.STATIC_ROOT) / "logo_heron_01.png"
    logo_signboard_relative = str(invoice.signboard.logo_signboard).replace("logos/", "")
    logo_signboard = Path(settings.STATIC_ROOT) / logo_signboard_relative

    # --- Creation du PDF ---
    pdf = HeronBasePDF(
        invoice=invoice,
        logo_heron=logo_heron,
        logo_signboard=logo_signboard,
    )
    pdf.add_page()

    # --- Largeurs de colonnes ---
    page_width = pdf.w - pdf.l_margin - pdf.r_margin
    col_supplier = page_width * 0.58      # FOURNISSEUR   58%
    col_total_ht = page_width * 0.14      # TOTAL HT      14%
    col_total_tva = page_width * 0.14     # TOTAL TVA     14%
    col_total_ttc = page_width * 0.14     # TOTAL TTC     14%

    # =========================================================================
    # 1. ENTETE (logos + adresses + meta facture)
    # =========================================================================
    pdf.draw_entete()
    pdf.ln(3)

    # =========================================================================
    # 2. BANNIERE DE TITRE
    # =========================================================================
    title_text = (
        f"R\u00e9capitulatif par fournisseurs - "
        f"{invoice.invoice_type_name} N\u00b0  {invoice.invoice_number}"
    )
    pdf.draw_title_banner(title_text)
    pdf.ln(3)

    # =========================================================================
    # 3. ENTETE DU TABLEAU
    # =========================================================================
    header_columns = [
        ("FOURNISSEUR", col_supplier, "L"),
        ("TOTAL HT", col_total_ht, "R"),
        ("TOTAL TVA", col_total_tva, "R"),
        ("TOTAL TTC", col_total_ttc, "R"),
    ]
    pdf.draw_table_header(header_columns)

    # =========================================================================
    # 4. LIGNES DE DONNEES (class "lignes")
    # =========================================================================
    for supplier in suppliers:
        net_amount = supplier.get("net_amount")
        vat_amount = supplier.get("vat_amount")
        amount_with_vat = supplier.get("amount_with_vat")

        cells = [
            (supplier.get("supplier_name", ""), col_supplier, "L"),
            (
                HeronBasePDF.format_number(net_amount) if net_amount else "",
                col_total_ht,
                "R",
            ),
            (
                HeronBasePDF.format_number(vat_amount) if vat_amount else "",
                col_total_tva,
                "R",
            ),
            (
                HeronBasePDF.format_number(amount_with_vat) if amount_with_vat else "",
                col_total_ttc,
                "R",
            ),
        ]
        pdf.draw_data_row(cells)

    # =========================================================================
    # 5. LIGNE TOTAUX (fond noir, texte blanc - meme style que l'entete)
    # =========================================================================
    sum_net = sum(s.get("net_amount", 0) or 0 for s in suppliers)
    sum_vat = sum(s.get("vat_amount", 0) or 0 for s in suppliers)
    sum_ttc = sum(s.get("amount_with_vat", 0) or 0 for s in suppliers)

    totaux_columns = [
        ("TOTAUX", col_supplier, "R"),
        (HeronBasePDF.format_number(sum_net), col_total_ht, "R"),
        (HeronBasePDF.format_number(sum_vat), col_total_tva, "R"),
        (HeronBasePDF.format_number(sum_ttc), col_total_ttc, "R"),
    ]
    pdf.draw_table_header(totaux_columns)

    # =========================================================================
    # 6. FOOTER (email + hr + footer text)
    # =========================================================================
    pdf.ln(5)
    pdf.draw_footer_block()

    # --- Ecriture du fichier PDF ---
    pdf.output(str(pdf_path))