# pylint: disable=E0401,C0413
"""
FR : Module de g\u00e9n\u00e9ration des ent\u00eates de factures de marchandises en pdf (version fpdf2)
EN : Module for generating invoice headers for marchandises in pdf (fpdf2 version)

Commentaire:
    Reproduction fid\u00e8le du template WeasyPrint "pdf_marchandises_header.html"
    en utilisant fpdf2 via la classe HeronBasePDF.

    Structure du document :
    1. En-t\u00eate g\u00e9n\u00e9rique (logos + adresses + meta facture)
    2. Banni\u00e8re titre : "<type> N\u00b0 <numero>"
    3. Tableau principal des rubriques par taux de TVA
    4. Totaux HT / TVA / TTC
    5. Mode de paiement + \u00e9ch\u00e9ance
    6. Mentions l\u00e9gales
    7. Footer (email contact + bas de page)

created at: 2024-02-10
created by: Paulo ALVES

modified at: 2024-02-10
modified by: Paulo ALVES
"""
from pathlib import Path
from uuid import UUID

from django.conf import settings
from django.db import connection

from apps.invoices.models import SaleInvoice
from apps.invoices.sql_files.sql_marchandises import SQL_HEADER, SQL_RESUME_HEADER
from apps.invoices.bin.conf import DOMAIN
from apps.invoices.bin.fpdf2.pdf_base import HeronBasePDF
from apps.invoices.bin.fpdf2.pdf_styles import (
    COLOR_BLACK,
    COLOR_WHITE,
    COLOR_DARK_HEADER,
    COLOR_GRAY_BORDER,
    FONT_SIZE_DEFAULT,
    LINE_HEIGHT_HEADER,
    LINE_HEIGHT_ROW,
)


def marchandise_header_invoice_pdf(uuid_invoice: UUID, pdf_path: Path) -> None:
    """
    G\u00e9n\u00e9ration des ent\u00eates de factures de marchandises au format PDF (fpdf2).

    Reproduit fid\u00e8lement le template HTML "pdf_marchandises_header.html" :
    - En-t\u00eate g\u00e9n\u00e9rique (logos, adresses, m\u00e9ta-donn\u00e9es)
    - Banni\u00e8re titre
    - Tableau des rubriques avec ventilation par taux de TVA
    - Lignes de totaux HT, TVA, TTC
    - Paiement, mentions l\u00e9gales, footer

    :param uuid_invoice: uuid_identification de la facture
    :param pdf_path: Path du fichier pdf de sortie
    :return: None
    """

    with connection.cursor() as cursor:
        # On fait un filter et non pas un get, pour pouvoir utiliser les \u00e9l\u00e9ments
        # tels que "general_footer_invoices.html" et "general_style_invoices"
        invoices = SaleInvoice.objects.filter(uuid_identification=uuid_invoice)

        # HEADER
        cursor.execute(SQL_HEADER, {"uuid_invoice": uuid_invoice})
        columns_header = [col[0] for col in cursor.description]
        headers = [dict(zip(columns_header, row)) for row in cursor.fetchall()]

        # RESUME HEADER
        cursor.execute(SQL_RESUME_HEADER, {"uuid_invoice": uuid_invoice})
        columns_resume = [col[0] for col in cursor.description]
        resume = [dict(zip(columns_resume, row)) for row in cursor.fetchall()][0]

    invoice = invoices[0]

    # --- Chemins des logos ---
    logo_heron = Path(settings.STATIC_ROOT) / "logo_heron_01.png"
    logo_signboard = (
        Path(settings.STATIC_ROOT)
        / str(invoice.signboard.logo_signboard).replace("logos/", "")
    )

    # --- Construction du PDF ---
    fmt = HeronBasePDF.format_number
    pdf = HeronBasePDF(
        invoice=invoice,
        logo_heron=logo_heron,
        logo_signboard=logo_signboard,
    )
    pdf.add_page()

    # =========================================================================
    # 1. En-t\u00eate g\u00e9n\u00e9rique (logos + adresses + meta)
    # =========================================================================
    pdf.draw_entete()
    pdf.ln(3)

    # =========================================================================
    # 2. Banni\u00e8re titre
    # =========================================================================
    title_text = f"{invoice.invoice_type_name} N\u00b0 {invoice.invoice_number}"
    pdf.draw_title_banner(title_text)
    pdf.ln(3)

    # =========================================================================
    # 3. Tableau principal : en-t\u00eate des colonnes
    # =========================================================================
    page_width = pdf.w - pdf.l_margin - pdf.r_margin
    col_widths = [
        page_width * 0.22,  # RUBRIQUES
        page_width * 0.22,  # (vide)
        page_width * 0.14,  # BASE TVA 0%
        page_width * 0.14,  # BASE TVA 5,5%
        page_width * 0.14,  # BASE TVA 20%
        page_width * 0.14,  # TOTAL HT
    ]

    header_columns = [
        ("RUBRIQUES", col_widths[0], "L"),
        ("", col_widths[1], "L"),
        ("BASE TVA 0%", col_widths[2], "R"),
        ("BASE TVA 5,5%", col_widths[3], "R"),
        ("BASE TVA 20%", col_widths[4], "R"),
        ("TOTAL HT", col_widths[5], "R"),
    ]

    pdf.draw_table_header(header_columns)

    # =========================================================================
    # 4. Lignes de donn\u00e9es (class "lignes")
    # =========================================================================
    previous_base = None
    pdf.set_font(pdf._font_body, size=FONT_SIZE_DEFAULT)

    for header in headers:
        # Position Y avant la ligne (pour les bordures verticales)
        y_line = pdf.get_y()

        # Colonne 1 : base (bold, seulement si changement - ifchanged)
        current_base = header.get("base", "")
        if current_base != previous_base:
            pdf.set_font(pdf._font_header, "", FONT_SIZE_DEFAULT)
            pdf.cell(col_widths[0], LINE_HEIGHT_ROW, str(current_base))
            pdf.set_font(pdf._font_body, size=FONT_SIZE_DEFAULT)
            previous_base = current_base
        else:
            pdf.cell(col_widths[0], LINE_HEIGHT_ROW, "")

        # Colonne 2 : grouping_goods
        pdf.cell(col_widths[1], LINE_HEIGHT_ROW, str(header.get("grouping_goods", "")))

        # Colonnes 3-6 : montants format\u00e9s
        for col_idx, field in enumerate(
            ["net_amount_00", "net_amount_01", "net_amount_02", "net_amount"], start=2
        ):
            value = header.get(field)
            text = fmt(value) if value else ""
            pdf.cell(col_widths[col_idx], LINE_HEIGHT_ROW, text, align="R")

        pdf.ln()

        # Bordures internes entre les colonnes (trait vertical #dadada)
        y_bottom = pdf.get_y()
        pdf.set_draw_color(*COLOR_GRAY_BORDER)
        x_offset = pdf.l_margin + col_widths[0]
        for i in range(1, len(col_widths) - 1):
            pdf.line(x_offset, y_line, x_offset, y_bottom)
            x_offset += col_widths[i]
        pdf.set_draw_color(*COLOR_BLACK)

    # =========================================================================
    # 5. Ligne Total HT (fond noir, texte blanc - style "entete")
    # =========================================================================
    pdf.draw_table_header(
        [
            ("", col_widths[0], "L"),
            ("Total HT", col_widths[1], "R"),
            (fmt(resume.get("net_amount_00")), col_widths[2], "R"),
            (fmt(resume.get("net_amount_01")), col_widths[3], "R"),
            (fmt(resume.get("net_amount_02")), col_widths[4], "R"),
            (fmt(resume.get("net_amount")), col_widths[5], "R"),
        ],
        fill_color=COLOR_BLACK,
    )

    # =========================================================================
    # 6. Ligne Total TVA (fond #404040, texte blanc)
    # =========================================================================
    pdf.draw_table_header(
        [
            ("", col_widths[0], "L"),
            ("Total TVA", col_widths[1], "R"),
            (fmt(resume.get("vat_amount_00")), col_widths[2], "R"),
            (fmt(resume.get("vat_amount_01")), col_widths[3], "R"),
            (fmt(resume.get("vat_amount_02")), col_widths[4], "R"),
            (fmt(resume.get("vat_amount")), col_widths[5], "R"),
        ],
        fill_color=COLOR_DARK_HEADER,
    )

    # =========================================================================
    # 7. Ligne Total TTC (fond noir, texte blanc - style "entete")
    # =========================================================================
    pdf.draw_table_header(
        [
            ("", col_widths[0], "L"),
            ("Total TTC", col_widths[1], "R"),
            (fmt(resume.get("ttc_amount_00")), col_widths[2], "R"),
            (fmt(resume.get("ttc_amount_01")), col_widths[3], "R"),
            (fmt(resume.get("ttc_amount_02")), col_widths[4], "R"),
            (fmt(resume.get("amount_with_vat")), col_widths[5], "R"),
        ],
        fill_color=COLOR_BLACK,
    )

    pdf.ln(2)

    # =========================================================================
    # 8. Paiement
    # =========================================================================
    pdf.draw_paiement()

    # =========================================================================
    # 9. Mentions l\u00e9gales
    # =========================================================================
    pdf.draw_mentions_legales()

    # =========================================================================
    # 10. Footer
    # =========================================================================
    pdf.draw_footer_block()

    # --- Sauvegarde du PDF ---
    pdf.output(str(pdf_path))