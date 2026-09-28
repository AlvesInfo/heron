# pylint: disable=E0401,C0413
"""
FR : Module de generation des details de factures marchandises en pdf (version fpdf2)
EN : Module for generating invoice details for marchandises in pdf (fpdf2 version)
created at: 2024-02-10
created by: Paulo ALVES
"""
from collections import OrderedDict
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from django.conf import settings
from django.db import connection

from apps.invoices.models import SaleInvoice, EnteteDetails
from apps.invoices.sql_files.sql_marchandises import SQL_DETAILS
from apps.invoices.bin.conf import DOMAIN
from apps.invoices.bin.fpdf2.pdf_base import HeronBasePDF
from apps.invoices.bin.fpdf2.pdf_styles import (
    COLOR_BLACK,
    COLOR_WHITE,
    COLOR_GRAY_LIGHT,
    COLOR_GRAY_MEDIUM,
    COLOR_GRAY_BORDER,
    FONT_SIZE_SMALL,
    FONT_SIZE_SUPPLIER_NAME,
    FONT_SIZE_SUB_ENTRY,
    MARGIN_LANDSCAPE_TOP,
    MARGIN_LANDSCAPE_BOTTOM,
    MARGIN_LANDSCAPE_LEFT,
    MARGIN_LANDSCAPE_RIGHT,
    LINE_HEIGHT_SMALL,
    LINE_HEIGHT_ROW,
)

# =============================================================================
# Constantes de mise en page paysage (A4 landscape = 297 x 210 mm)
# =============================================================================
PAGE_WIDTH = 297
PAGE_HEIGHT = 210

# Largeurs de colonnes en pourcentage de la largeur utile (reproduit le CSS)
# td:first-child  -> 16.2%   (invoice_number)
# td:nth-child(2) ->  4.6%   (invoice_date)
# td:nth-child(n+3) -> 6.6%  (11 amount cols + total_ht = 12 cols)
COL_PCT_INVOICE = 16.2
COL_PCT_DATE = 4.6
COL_PCT_AMOUNT = 6.6  # pour chacune des 12 colonnes restantes

# Cle des colonnes dynamiques dans l'ordre attendu
AMOUNT_KEYS = ("MO", "MS", "VE", "COT", "AU", "PI", "AC", "AO", "CO", "PO", "DI")


def _compute_col_widths(usable_width: float) -> list[float]:
    """Retourne la liste ordonnee des largeurs de colonnes en mm.

    Ordre : invoice_number | invoice_date | MO..DI (11) | total_ht
    Total = 14 colonnes.
    """
    w_invoice = usable_width * COL_PCT_INVOICE / 100
    w_date = usable_width * COL_PCT_DATE / 100
    w_amount = usable_width * COL_PCT_AMOUNT / 100
    # 11 dynamic amount cols + 1 total_ht col = 12 amount cols
    return [w_invoice, w_date] + [w_amount] * 12


def _default_if_zero(value: Decimal) -> str:
    """Reproduit le filtre Django |default_if_zero : renvoie '' si la valeur est 0."""
    if value == 0 or value is None:
        return ""
    return HeronBasePDF.format_number(value)


def _group_suppliers(rows: list[dict]) -> OrderedDict:
    """Regroupe les lignes par supplier_name (equivalent de {% regroup %} Django).

    Retourne un OrderedDict preservant l'ordre d'apparition.
    """
    groups: OrderedDict[str, list[dict]] = OrderedDict()
    for row in rows:
        name = row["supplier_name"]
        groups.setdefault(name, []).append(row)
    return groups


def _sum_field(rows: list[dict], field: str) -> Decimal:
    """Somme un champ numerique sur une liste de dicts."""
    return sum((row.get(field) or Decimal(0)) for row in rows)


def marchandise_details_invoice_pdf(uuid_invoice: UUID, pdf_path: Path) -> None:
    """
    Generation du PDF paysage 'Details de la facture marchandises' via fpdf2.

    Reproduit fidelement le template WeasyPrint ``pdf_marchandises_details.html``.

    :param uuid_invoice: uuid_identification de la facture
    :param pdf_path: chemin de sortie du fichier PDF
    """

    # =========================================================================
    # 1. Requetes en base
    # =========================================================================
    with connection.cursor() as cursor:
        invoices = SaleInvoice.objects.filter(uuid_identification=uuid_invoice)
        invoice = invoices[0]

        cursor.execute(SQL_DETAILS, {"uuid_invoice": uuid_invoice})
        columns_details = [col[0] for col in cursor.description]
        suppliers = [dict(zip(columns_details, row)) for row in cursor.fetchall()]

        entetes = list(EnteteDetails.objects.all().values_list("column_name", flat=True))

    # =========================================================================
    # 2. Donnees derivees
    # =========================================================================
    name_cct = invoice.parties.name_cct if invoice.parties else ""
    invoice_number = invoice.invoice_number
    invoice_date = invoice.invoice_date.strftime("%d/%m/%Y") if invoice.invoice_date else ""
    invoice_type_name = invoice.invoice_type_name or ""
    logo_signboard_name = (
        str(invoice.signboard.logo_signboard).replace("logos/", "")
        if invoice.signboard and invoice.signboard.logo_signboard
        else ""
    )

    supplier_groups = _group_suppliers(suppliers)

    # =========================================================================
    # 3. Creation du PDF paysage
    # =========================================================================
    pdf = HeronBasePDF(orientation="L")
    pdf.set_margins(
        left=MARGIN_LANDSCAPE_LEFT,
        top=MARGIN_LANDSCAPE_TOP,
        right=MARGIN_LANDSCAPE_RIGHT,
    )
    pdf.set_auto_page_break(auto=True, margin=MARGIN_LANDSCAPE_BOTTOM)
    pdf.add_page()

    usable_width = PAGE_WIDTH - MARGIN_LANDSCAPE_LEFT - MARGIN_LANDSCAPE_RIGHT
    col_widths = _compute_col_widths(usable_width)

    # =========================================================================
    # 4. Logo section (pdf_generic_logo.html)
    # =========================================================================
    static_root = Path(str(settings.STATIC_ROOT))
    logo_heron_path = static_root / "logo_heron_01.png"
    logo_signboard_path = static_root / logo_signboard_name if logo_signboard_name else None

    y_start = pdf.get_y() + 5  # marge haute visuelle ~20px -> ~5mm
    pdf.set_y(y_start)

    if logo_heron_path.is_file():
        pdf.image(str(logo_heron_path), x=MARGIN_LANDSCAPE_LEFT + 2, y=pdf.get_y(), w=65)

    if logo_signboard_path and logo_signboard_path.is_file():
        pdf.image(str(logo_signboard_path), x=MARGIN_LANDSCAPE_LEFT + 72, y=pdf.get_y(), w=65)

    pdf.set_y(pdf.get_y() + 18)

    # Trait horizontal (hr)
    pdf.set_draw_color(*COLOR_BLACK)
    pdf.set_line_width(0.3)
    pdf.line(MARGIN_LANDSCAPE_LEFT, pdf.get_y(), PAGE_WIDTH - MARGIN_LANDSCAPE_RIGHT, pdf.get_y())
    pdf.ln(2)

    # =========================================================================
    # 5. Bandeau titre (entete)
    # =========================================================================
    pdf.set_font(pdf._font_header, "", FONT_SIZE_SMALL)
    pdf.set_fill_color(*COLOR_BLACK)
    pdf.set_text_color(*COLOR_WHITE)

    title_text = (
        f"Maison : {name_cct} - "
        f"Details de la facture n\u00b0 : {invoice_number} - "
        f"Date de la facture : {invoice_date}"
    )
    pdf.cell(usable_width, LINE_HEIGHT_ROW, title_text, border=0, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(*COLOR_BLACK)
    pdf.ln(2)

    # =========================================================================
    # 6. Boucle par groupe fournisseur
    # =========================================================================
    for supplier_name, group_rows in supplier_groups.items():
        # Espacement avant chaque groupe (~20px -> ~5mm)
        pdf.ln(5)

        # -----------------------------------------------------------------
        # 6a. Ligne nom fournisseur (class=fournisseur)
        # -----------------------------------------------------------------
        pdf.set_font(pdf._font_header, "", FONT_SIZE_SUPPLIER_NAME)
        pdf.set_fill_color(*COLOR_GRAY_MEDIUM)
        pdf.set_text_color(*COLOR_BLACK)
        pdf.set_draw_color(212, 212, 212)

        pdf.cell(
            usable_width,
            LINE_HEIGHT_ROW + 1,
            supplier_name.upper(),
            border=1,
            align="C",
            fill=True,
            new_x="LMARGIN",
            new_y="NEXT",
        )

        # -----------------------------------------------------------------
        # 6b. Sous-entete (class=sousEntete)
        # -----------------------------------------------------------------
        pdf.set_font(pdf._font_header, "", FONT_SIZE_SUB_ENTRY)
        pdf.set_fill_color(*COLOR_GRAY_LIGHT)
        pdf.set_draw_color(212, 212, 212)

        sub_headers = [f"N\u00b0 {invoice_type_name}", "DATE FACTURE"] + [e.upper() for e in entetes] + ["TOTAL HT"]

        for i, header in enumerate(sub_headers):
            pdf.cell(
                col_widths[i],
                LINE_HEIGHT_ROW,
                header,
                border=1,
                align="C",
                fill=True,
            )
        pdf.ln()

        # -----------------------------------------------------------------
        # 6c. Lignes de donnees (class=bordures)
        # -----------------------------------------------------------------
        pdf.set_font(pdf._font_body, "", FONT_SIZE_SMALL)
        pdf.set_draw_color(*COLOR_GRAY_BORDER)

        for row in group_rows:
            # Verifier le saut de page
            if pdf.get_y() + LINE_HEIGHT_SMALL > PAGE_HEIGHT - MARGIN_LANDSCAPE_BOTTOM:
                pdf.add_page()

            # Invoice number (left aligned)
            pdf.cell(
                col_widths[0],
                LINE_HEIGHT_SMALL,
                str(row.get("invoice_number", "")),
                border="LR",
                align="L",
            )

            # Invoice date (centered, format dd/mm/yy)
            raw_date = row.get("invoice_date")
            date_str = raw_date.strftime("%d/%m/%y") if raw_date else ""
            pdf.cell(
                col_widths[1],
                LINE_HEIGHT_SMALL,
                date_str,
                border="LR",
                align="C",
            )

            # 11 colonnes dynamiques MO..DI (right aligned, empty if 0)
            for j, key in enumerate(AMOUNT_KEYS):
                val = row.get(key) or Decimal(0)
                display = HeronBasePDF.format_number(val) if val else ""
                pdf.cell(
                    col_widths[2 + j],
                    LINE_HEIGHT_SMALL,
                    display,
                    border="LR",
                    align="R",
                )

            # Total HT (right aligned, fond gris #ededed)
            total_ht = row.get("total_ht") or Decimal(0)
            pdf.set_fill_color(*COLOR_GRAY_LIGHT)
            pdf.cell(
                col_widths[13],
                LINE_HEIGHT_SMALL,
                HeronBasePDF.format_number(total_ht),
                border="LR",
                align="R",
                fill=True,
            )
            pdf.ln()

        # -----------------------------------------------------------------
        # 6d. Ligne total par fournisseur (class=bordures totaux)
        # -----------------------------------------------------------------
        if pdf.get_y() + LINE_HEIGHT_ROW > PAGE_HEIGHT - MARGIN_LANDSCAPE_BOTTOM:
            pdf.add_page()

        pdf.set_font(pdf._font_header, "", FONT_SIZE_SMALL)
        pdf.set_fill_color(*COLOR_GRAY_LIGHT)
        pdf.set_draw_color(212, 212, 212)

        # "TOTAL supplier_name" sur les 2 premieres colonnes
        total_label_w = col_widths[0] + col_widths[1]
        pdf.cell(
            total_label_w,
            LINE_HEIGHT_ROW,
            f"TOTAL {supplier_name.upper()}",
            border=1,
            align="R",
            fill=True,
        )

        # Sommes par colonne dynamique
        for key in AMOUNT_KEYS:
            col_sum = _sum_field(group_rows, key)
            pdf.cell(
                col_widths[2 + list(AMOUNT_KEYS).index(key)],
                LINE_HEIGHT_ROW,
                _default_if_zero(col_sum),
                border=1,
                align="R",
                fill=True,
            )

        # Total HT fournisseur
        total_ht_sum = _sum_field(group_rows, "total_ht")
        pdf.cell(
            col_widths[13],
            LINE_HEIGHT_ROW,
            HeronBasePDF.format_number(total_ht_sum),
            border=1,
            align="R",
            fill=True,
        )
        pdf.ln()

    # =========================================================================
    # 7. TOTAL GENERAL (class=totalGeneral)
    # =========================================================================
    pdf.ln(5)

    if pdf.get_y() + LINE_HEIGHT_ROW > PAGE_HEIGHT - MARGIN_LANDSCAPE_BOTTOM:
        pdf.add_page()

    pdf.set_font(pdf._font_header, "", FONT_SIZE_SMALL)
    pdf.set_fill_color(*COLOR_GRAY_LIGHT)
    pdf.set_draw_color(212, 212, 212)

    # "TOTAL GENERAL" sur 20.8% de la largeur utile (= col1 + col2 en CSS totalGeneral)
    total_general_label_w = col_widths[0] + col_widths[1]
    pdf.cell(
        total_general_label_w,
        LINE_HEIGHT_ROW,
        "TOTAL GENERAL",
        border=1,
        align="R",
        fill=True,
    )

    # Sommes globales par colonne dynamique
    for key in AMOUNT_KEYS:
        grand_sum = _sum_field(suppliers, key)
        pdf.cell(
            col_widths[2 + list(AMOUNT_KEYS).index(key)],
            LINE_HEIGHT_ROW,
            _default_if_zero(grand_sum),
            border=1,
            align="R",
            fill=True,
        )

    # Total HT general
    grand_total_ht = _sum_field(suppliers, "total_ht")
    pdf.cell(
        col_widths[13],
        LINE_HEIGHT_ROW,
        HeronBasePDF.format_number(grand_total_ht),
        border=1,
        align="R",
        fill=True,
    )
    pdf.ln()

    # =========================================================================
    # 8. Sauvegarde
    # =========================================================================
    pdf.output(str(pdf_path))