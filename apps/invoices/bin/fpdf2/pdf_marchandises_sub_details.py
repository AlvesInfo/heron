# pylint: disable=E0401,C0413
"""
FR : Module de generation des sous-details de factures marchandises en pdf (version fpdf2)
EN : Module for generating invoice sub-details for marchandises in pdf (fpdf2 version)

Commentaire:
    Reproduction fidele du template HTML pdf_marchandises_sub_details.html
    avec les styles de general_style_sub_details.html, en utilisant fpdf2.

    Donnees regroupees par supplier_name -> invoice_number -> delivery_number.

created at: 2024-02-10
created by: Paulo ALVES

modified at: 2024-02-10
modified by: Paulo ALVES
"""
from collections import OrderedDict
from pathlib import Path
from uuid import UUID

from django.db import connection
from django.conf import settings

from apps.invoices.models import SaleInvoice
from apps.invoices.sql_files.sql_marchandises import SQL_SUB_DETAILS
from apps.invoices.bin.conf import DOMAIN
from apps.invoices.bin.fpdf2.pdf_base import HeronBasePDF
from apps.invoices.bin.fpdf2.pdf_styles import (
    COLOR_BLACK,
    COLOR_WHITE,
    COLOR_GRAY_LIGHT,
    COLOR_GRAY_MEDIUM,
    COLOR_GRAY_DARK,
    COLOR_GRAY_BORDER,
    COLOR_GRAY_BG_BL,
    FONT_SIZE_DEFAULT,
    FONT_SIZE_TITLE,
    FONT_SIZE_SUPPLIER_NAME,
    FONT_SIZE_SUB_TOTAL,
    FONT_SIZE_SUB_ENTRY,
    LINE_HEIGHT_HEADER,
    LINE_HEIGHT_ROW,
    MARGIN_PORTRAIT,
)


# =====================================================================
# Constantes de largeur de colonnes (en % de la largeur utile)
# =====================================================================
COL_PCT_GROUPING = 0.14     # Collection : 14%
COL_PCT_ARTICLE = 0.57      # Article    : 57%
COL_PCT_QTY = 0.07          # Qte        :  7%
COL_PCT_UNIT_PRICE = 0.10   # PU         : 10%
COL_PCT_TOTAL_HT = 0.12     # Total HT   : 12%

# Largeur de la zone s/total et total (4 premieres colonnes = 88%)
COL_PCT_LABEL_SPAN = COL_PCT_GROUPING + COL_PCT_ARTICLE + COL_PCT_QTY + COL_PCT_UNIT_PRICE


# =====================================================================
# Regroupement des donnees
# =====================================================================
def _regroup_data(rows):
    """
    Regroupe les lignes (list[dict]) par :
      supplier_name -> invoice_number -> delivery_number

    Retourne un OrderedDict :
        {
            supplier_name: OrderedDict({
                invoice_number: {
                    "invoice_date": ...,
                    "deliveries": OrderedDict({
                        delivery_number: [line, ...],
                    }),
                    "lines": [line, ...],  # toutes les lignes pour sous-total
                },
            }),
        }
    """
    suppliers = OrderedDict()

    for row in rows:
        s_name = row["supplier_name"] or ""
        i_num = row["invoice_number"] or ""
        d_num = row["delivery_number"] or ""

        if s_name not in suppliers:
            suppliers[s_name] = OrderedDict()

        invoices = suppliers[s_name]

        if i_num not in invoices:
            invoices[i_num] = {
                "invoice_date": row["invoice_date"],
                "deliveries": OrderedDict(),
                "lines": [],
            }

        inv_data = invoices[i_num]
        inv_data["lines"].append(row)

        if d_num not in inv_data["deliveries"]:
            inv_data["deliveries"][d_num] = []

        inv_data["deliveries"][d_num].append(row)

    return suppliers


def _sum_net_amount(lines):
    """Somme du champ net_amount sur une liste de dicts."""
    return sum((row.get("net_amount") or 0) for row in lines)


# =====================================================================
# Classe PDF
# =====================================================================
class SubDetailsPDF(HeronBasePDF):
    """
    PDF reproduisant pdf_marchandises_sub_details.html.
    Portrait A4, marges CSS : 0 0 5mm 0 (adaptees en 5mm tout autour
    pour garder de la lisibilite dans fpdf2 ; bottom-margin specifique).
    """

    def __init__(self, invoice, logo_heron, logo_signboard):
        super().__init__(orientation="P", invoice=invoice, logo_heron=logo_heron, logo_signboard=logo_signboard)
        # Marges CSS @page : margin: 0 0 5mm 0
        # En fpdf2 on garde une marge gauche/droite minimale pour la lisibilite
        left_right = 5
        self.set_margins(left_right, 5, left_right)
        self.set_auto_page_break(auto=True, margin=10)

    # ------------------------------------------------------------------
    # Footer : compteur de pages en bas a droite
    # ------------------------------------------------------------------
    def footer(self):
        """Reproduit general_style_counter_pages.html : page / pages en bas a droite."""
        self.set_y(-10)
        self.set_font(self._font_body, "", FONT_SIZE_DEFAULT)
        self.set_text_color(*COLOR_BLACK)
        page_text = f"{self.page_no()}/{{nb}}"
        self.cell(0, 5, page_text, align="R")

    # ------------------------------------------------------------------
    # Utilitaire : largeurs de colonnes absolues
    # ------------------------------------------------------------------
    def _col_widths(self):
        """Retourne les largeurs de colonnes en mm."""
        pw = self.w - self.l_margin - self.r_margin
        return (
            pw * COL_PCT_GROUPING,
            pw * COL_PCT_ARTICLE,
            pw * COL_PCT_QTY,
            pw * COL_PCT_UNIT_PRICE,
            pw * COL_PCT_TOTAL_HT,
        )

    def _label_span_width(self):
        """Largeur des 4 premieres colonnes (pour sous-totaux / totaux)."""
        pw = self.w - self.l_margin - self.r_margin
        return pw * COL_PCT_LABEL_SPAN

    def _total_ht_width(self):
        """Largeur de la colonne Total HT."""
        pw = self.w - self.l_margin - self.r_margin
        return pw * COL_PCT_TOTAL_HT

    # ------------------------------------------------------------------
    # Dessin : ligne fournisseur (fond noir, texte blanc, centre, uppercase)
    # ------------------------------------------------------------------
    def _draw_supplier_row(self, supplier_name):
        """Ligne .fournisseur : fond noir, texte blanc, centre, uppercase, ClanMedium."""
        pw = self.w - self.l_margin - self.r_margin
        self.set_font(self._font_header, "", FONT_SIZE_SUPPLIER_NAME)
        self.set_fill_color(*COLOR_BLACK)
        self.set_text_color(*COLOR_WHITE)
        self.cell(
            pw, LINE_HEIGHT_HEADER,
            (supplier_name or "").upper(),
            align="C",
            fill=True,
        )
        self.ln()
        self.set_text_color(*COLOR_BLACK)

    # ------------------------------------------------------------------
    # Dessin : ligne detail facture (#ededed -> en fait #dbdbdb dans inline)
    # ------------------------------------------------------------------
    def _draw_invoice_detail_row(self, invoice_type_name, invoice_number, invoice_date):
        """Ligne .detailsFacture : fond #dbdbdb, ClanMedium."""
        pw = self.w - self.l_margin - self.r_margin
        date_str = invoice_date.strftime("%d/%m/%y") if invoice_date else ""
        text = f"{invoice_type_name} n\u00b0 : {invoice_number} - du {date_str}"

        self.set_font(self._font_header, "", FONT_SIZE_DEFAULT)
        self.set_fill_color(*COLOR_GRAY_MEDIUM)
        self.set_text_color(*COLOR_BLACK)
        self.cell(pw, LINE_HEIGHT_ROW + 1, f"  {text}", align="L", fill=True)
        self.ln()

    # ------------------------------------------------------------------
    # Dessin : sous-entete de colonnes (#dbdbdb, ClanMedium, centre)
    # ------------------------------------------------------------------
    def _draw_sub_header(self):
        """Ligne .sousEntete : fond #dbdbdb, ClanMedium, centre, font-size 0.9em."""
        w_grp, w_art, w_qty, w_pu, w_ht = self._col_widths()

        self.set_font(self._font_header, "", FONT_SIZE_SUB_ENTRY)
        self.set_fill_color(*COLOR_GRAY_MEDIUM)
        self.set_text_color(*COLOR_BLACK)

        self.cell(w_grp, LINE_HEIGHT_ROW, "  Collection", align="L", fill=True)
        self.cell(w_art, LINE_HEIGHT_ROW, " Article", align="L", fill=True)
        self.cell(w_qty, LINE_HEIGHT_ROW, "Qt\u00e9", align="R", fill=True)
        self.cell(w_pu, LINE_HEIGHT_ROW, "PU  ", align="R", fill=True)
        self.cell(w_ht, LINE_HEIGHT_ROW, "Total HT  ", align="R", fill=True)
        self.ln()

    # ------------------------------------------------------------------
    # Dessin : ligne BL (#f5f5f5, ClanMedium)
    # ------------------------------------------------------------------
    def _draw_delivery_row(self, delivery_number, delivery_date=None):
        """Ligne .borduresBL : fond #f5f5f5, ClanMedium."""
        pw = self.w - self.l_margin - self.r_margin
        text = f"BL n\u00b0 : {delivery_number}"
        if delivery_date:
            date_str = delivery_date.strftime("%d/%m/%y") if hasattr(delivery_date, "strftime") else str(delivery_date)
            text += f" - du {date_str}"

        self.set_font(self._font_header, "", FONT_SIZE_SUB_ENTRY)
        self.set_fill_color(*COLOR_GRAY_BG_BL)
        self.set_text_color(*COLOR_BLACK)
        self.cell(pw, LINE_HEIGHT_ROW + 1, f"  {text}", align="L", fill=True)
        self.ln()

    # ------------------------------------------------------------------
    # Dessin : ligne de donnees (bordures #dadada, 0.9em)
    # ------------------------------------------------------------------
    def _draw_data_line(self, line):
        """
        Ligne .bordures : border 1px solid #dadada, font-size 0.9em.
        L'article peut contenir plusieurs lignes (client_name, serial_number).
        """
        w_grp, w_art, w_qty, w_pu, w_ht = self._col_widths()

        grouping = str(line.get("grouping_goods") or "")
        article = str(line.get("article") or "")
        client_name = line.get("client_name") or ""
        serial_number = line.get("serial_number") or ""

        qty_text = self.format_number(line.get("qty"), 0)
        pu_text = self.format_number(line.get("net_unit_price"), 2)
        ht_text = self.format_number(line.get("net_amount"), 2)

        # Construction du texte multi-lignes pour la colonne article
        article_lines = [article]
        if client_name:
            article_lines.append(f"Client : {client_name}")
        if serial_number:
            article_lines.append(f"N\u00b0 de s\u00e9rie {serial_number}")

        article_text = "\n".join(article_lines)

        # Calcul de la hauteur necessaire pour la cellule article
        self.set_font(self._font_body, "", FONT_SIZE_SUB_ENTRY)
        nb_lines_article = len(article_lines)
        row_h = LINE_HEIGHT_ROW
        cell_h = max(row_h, nb_lines_article * row_h)

        # Verification de saut de page
        if self.get_y() + cell_h > self.h - 10:
            self.add_page()

        self.set_draw_color(*COLOR_GRAY_BORDER)
        y_before = self.get_y()
        x_start = self.get_x()

        # Colonne grouping_goods (vertical-align: top)
        self.set_font(self._font_body, "", FONT_SIZE_SUB_ENTRY)
        self.rect(x_start, y_before, w_grp, cell_h)
        self.set_xy(x_start + 1, y_before)
        self.cell(w_grp - 1, row_h, grouping, align="L")

        # Colonne article (multi-cell, vertical-align: top)
        x_art = x_start + w_grp
        self.rect(x_art, y_before, w_art, cell_h)
        self.set_xy(x_art + 1, y_before)
        for i, a_line in enumerate(article_lines):
            self.set_xy(x_art + 1, y_before + i * row_h)
            self.cell(w_art - 2, row_h, a_line, align="L")

        # Colonne qty (vertical-align: bottom)
        x_qty = x_art + w_art
        self.rect(x_qty, y_before, w_qty, cell_h)
        self.set_xy(x_qty, y_before + cell_h - row_h)
        self.cell(w_qty - 1, row_h, qty_text, align="R")

        # Colonne net_unit_price (vertical-align: bottom)
        x_pu = x_qty + w_qty
        self.rect(x_pu, y_before, w_pu, cell_h)
        self.set_xy(x_pu, y_before + cell_h - row_h)
        self.cell(w_pu - 1, row_h, pu_text, align="R")

        # Colonne net_amount (vertical-align: bottom)
        x_ht = x_pu + w_pu
        self.rect(x_ht, y_before, w_ht, cell_h)
        self.set_xy(x_ht, y_before + cell_h - row_h)
        self.cell(w_ht - 1, row_h, ht_text, align="R")

        self.set_xy(x_start, y_before + cell_h)

    # ------------------------------------------------------------------
    # Dessin : ligne sous-total (#dbdbdb, 0.8em, bold)
    # ------------------------------------------------------------------
    def _draw_sub_total_row(self, invoice_number, total):
        """Ligne .sousTotaux : fond #dbdbdb, bold, 0.8em."""
        label_w = self._label_span_width()
        ht_w = self._total_ht_width()

        self.set_font(self._font_header, "B", FONT_SIZE_SUB_TOTAL)
        self.set_fill_color(*COLOR_GRAY_MEDIUM)
        self.set_text_color(*COLOR_BLACK)

        label_text = f"Sous-total - Facture n\u00b0 : {invoice_number}"
        self.cell(label_w, LINE_HEIGHT_ROW, f"  {label_text}", align="L", fill=True)
        self.cell(ht_w, LINE_HEIGHT_ROW, f"{self.format_number(total, 2)}  ", align="R", fill=True)
        self.ln()

    # ------------------------------------------------------------------
    # Dessin : ligne total fournisseur (#bebdbd, 0.8em, bold)
    # ------------------------------------------------------------------
    def _draw_supplier_total_row(self, supplier_name, total):
        """Ligne .totaux : fond #bebdbd, bold, 0.8em."""
        label_w = self._label_span_width()
        ht_w = self._total_ht_width()

        self.set_font(self._font_header, "B", FONT_SIZE_SUB_TOTAL)
        self.set_fill_color(*COLOR_GRAY_DARK)
        self.set_text_color(*COLOR_BLACK)

        label_text = f"Total - {supplier_name}"
        self.cell(label_w, LINE_HEIGHT_ROW, f"  {label_text}", align="L", fill=True)
        self.cell(ht_w, LINE_HEIGHT_ROW, f"{self.format_number(total, 2)}  ", align="R", fill=True)
        self.ln()

    # ------------------------------------------------------------------
    # Construction complete du document
    # ------------------------------------------------------------------
    def build(self, sub_details):
        """
        Construit le PDF complet a partir des donnees brutes.
        :param sub_details: list[dict] provenant de SQL_SUB_DETAILS
        """
        self.alias_nb_pages()
        self.add_page()

        inv = self.invoice

        # --- Entete : logos + adresses + meta ---
        self.draw_entete()
        self.ln(3)

        # --- Banniere de titre ---
        title = (
            f"Sous D\u00e9tails {inv.invoice_type_name} "
            f"n\u00b0 : {inv.invoice_number}"
        )
        self.draw_title_banner(title)
        self.ln(3)

        # --- Regroupement des donnees ---
        grouped = _regroup_data(sub_details)
        invoice_type_name = inv.invoice_type_name or ""

        for supplier_name, invoices_dict in grouped.items():
            # Verification saut de page avant le bloc fournisseur
            if self.get_y() > self.h - 30:
                self.add_page()

            # Ligne fournisseur
            self._draw_supplier_row(supplier_name)

            supplier_lines = []

            for invoice_number, inv_data in invoices_dict.items():
                # Espacement avant la facture
                self.ln(2)

                # Ligne detail facture
                self._draw_invoice_detail_row(
                    invoice_type_name, invoice_number, inv_data["invoice_date"]
                )

                # Sous-entete colonnes
                self._draw_sub_header()

                # Parcours des livraisons
                for delivery_number, delivery_lines in inv_data["deliveries"].items():
                    # Ligne BL si delivery_number est non vide
                    if delivery_number:
                        delivery_date = delivery_lines[0].get("delivery_date")
                        self._draw_delivery_row(delivery_number, delivery_date)

                    # Lignes de donnees
                    for line in delivery_lines:
                        self._draw_data_line(line)

                # Sous-total facture
                invoice_total = _sum_net_amount(inv_data["lines"])
                self._draw_sub_total_row(invoice_number, invoice_total)

                supplier_lines.extend(inv_data["lines"])

            # Total fournisseur
            supplier_total = _sum_net_amount(supplier_lines)
            self._draw_supplier_total_row(supplier_name, supplier_total)
            self.ln(3)


# =====================================================================
# Fonction principale
# =====================================================================
def marchandise_sub_details_invoice_pdf(uuid_invoice: UUID, pdf_path: Path) -> None:
    """
    Generation des pages sous-details marchandises en PDF via fpdf2.

    :param uuid_invoice: uuid_identification de la facture
    :param pdf_path: chemin de sortie du fichier PDF
    """
    with connection.cursor() as cursor:
        # Recuperation de la facture
        invoices = SaleInvoice.objects.filter(uuid_identification=uuid_invoice)
        invoice = invoices[0]

        # Execution de la requete SQL_SUB_DETAILS
        cursor.execute(SQL_SUB_DETAILS, {"uuid_invoice": uuid_invoice})
        columns = [col[0] for col in cursor.description]
        sub_details = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Chemins des logos
        logo_heron = str(Path(settings.STATIC_ROOT) / "logo_heron_01.png")
        logo_signboard_name = str(invoice.signboard.logo_signboard).replace("logos/", "")
        logo_signboard = str(Path(settings.STATIC_ROOT) / logo_signboard_name) if logo_signboard_name else ""

        # Construction du PDF
        pdf = SubDetailsPDF(invoice, logo_heron, logo_signboard)
        pdf.build(sub_details)
        pdf.output(str(pdf_path))


if __name__ == "__main__":
    uuid_invoice_to_pdf = UUID("8b4ac234-e03e-4ac6-bf9e-491a40cab635")
    sale = SaleInvoice.objects.get(uuid_identification=uuid_invoice_to_pdf)

    sub_path = Path(settings.SALES_INVOICES_FILES_DIR) / f"{sale.cct}_sub_marchandise_fpdf2.pdf"
    marchandise_sub_details_invoice_pdf(uuid_invoice=uuid_invoice_to_pdf, pdf_path=sub_path)