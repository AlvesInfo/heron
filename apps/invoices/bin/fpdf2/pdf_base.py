# pylint: disable=E0401,C0413
"""
FR : Classe de base PDF pour fpdf2 reproduisant les styles des factures
EN : Base PDF class for fpdf2 reproducing invoice styles

Commentaire:
    Reproduction fidele des styles definis dans les templates HTML/CSS :
    - general_style_invoices.html (header, suppliers, page portrait A4)
    - general_style_details.html (details, page paysage A4)
    - general_style_sub_details.html (sub_details, page portrait A4)
    - general_style_counter_pages.html (compteur de pages)
    - pdf_generic_entete.html (logos, adresses, metadonnees facture)
    - pdf_generic_footer_invoices.html (footer email + mentions legales)

created at: 2024-02-10
created by: Paulo ALVES

modified at: 2024-02-10
modified by: Paulo ALVES
"""
import os
from pathlib import Path
from decimal import Decimal

from fpdf import FPDF

from apps.invoices.bin.fpdf2.pdf_styles import (
    COLOR_BLACK,
    COLOR_WHITE,
    COLOR_GRAY_LIGHT,
    COLOR_GRAY_MEDIUM,
    COLOR_GRAY_DARK,
    COLOR_GRAY_BORDER,
    COLOR_GRAY_BG_BL,
    COLOR_DARK_HEADER,
    COLOR_RED,
    FONT_SIZE_DEFAULT,
    FONT_SIZE_SMALL,
    FONT_SIZE_TITLE,
    FONT_SIZE_SUPPLIER_NAME,
    FONT_SIZE_FOOTER,
    FONT_SIZE_FOOTER_SMALL,
    FONT_SIZE_SUB_TOTAL,
    FONT_SIZE_SUB_ENTRY,
    MARGIN_PORTRAIT,
    MARGIN_LANDSCAPE_TOP,
    MARGIN_LANDSCAPE_BOTTOM,
    MARGIN_LANDSCAPE_LEFT,
    MARGIN_LANDSCAPE_RIGHT,
    LINE_HEIGHT_HEADER,
    LINE_HEIGHT_ROW,
    LINE_HEIGHT_SMALL,
    LINE_HEIGHT_FOOTER,
    CELL_PADDING,
    CELL_PADDING_LEFT,
    CELL_PADDING_RIGHT,
)


class HeronBasePDF(FPDF):
    """
    Classe de base PDF pour fpdf2 reproduisant les styles CSS des factures Heron.

    Utilise les polices ClanBook (corps de texte, equivalent de font-family:'ClanBook')
    et ClanMedium (entetes, equivalent de font-family:'ClanMedium') chargees depuis
    le repertoire des fichiers statiques (settings.STATIC_ROOT -> files/static/).

    Retombe sur Helvetica si les fichiers OTF ne sont pas trouves.

    Templates HTML reproduits :
        - pdf_generic_entete.html : logos + adresses + meta facture
        - pdf_generic_footer_invoices.html : email contact + hr + mentions legales
        - general_style_invoices.html : styles portrait (.entete, .lignes, .footer)
        - general_style_details.html : styles paysage (.fournisseur, .sousEntete, .totaux)
        - general_style_counter_pages.html : compteur page/total en bas a droite

    :param orientation: "P" pour portrait (21x29.7cm) ou "L" pour paysage (29.7x21cm)
    :param fonts_dir: repertoire contenant ClanBook.otf et ClanMedium.otf
                      (par defaut : settings.STATIC_ROOT)
    """

    # Noms logiques des polices
    FONT_BODY = "ClanBook"
    FONT_HEADER = "ClanMedium"
    FONT_FALLBACK = "Helvetica"

    def __init__(self, orientation="P", fonts_dir=None, invoice=None,
                 logo_heron=None, logo_signboard=None):
        super().__init__(orientation=orientation, unit="mm", format="A4")

        # ----------------------------------------------------------------
        # Objet facture et logos (stockes pour les methodes sans argument)
        # ----------------------------------------------------------------
        self.invoice = invoice
        self.logo_heron = logo_heron
        self.logo_signboard = logo_signboard

        # ----------------------------------------------------------------
        # Marges selon l'orientation (reproduction du CSS @page)
        # ----------------------------------------------------------------
        if orientation.upper() == "L":
            # @page { size: 29.7cm 21cm; margin: 0 0 5mm 0; }
            self.set_margins(
                MARGIN_LANDSCAPE_LEFT,
                MARGIN_LANDSCAPE_TOP,
                MARGIN_LANDSCAPE_RIGHT,
            )
            self.set_auto_page_break(auto=True, margin=MARGIN_LANDSCAPE_BOTTOM)
        else:
            # @page { size: 21cm 29.7cm; margin: 10mm 10mm 10mm 10mm; }
            self.set_margins(MARGIN_PORTRAIT, MARGIN_PORTRAIT, MARGIN_PORTRAIT)
            self.set_auto_page_break(auto=True, margin=MARGIN_PORTRAIT + 5)

        # ----------------------------------------------------------------
        # Chargement des polices OTF
        # ----------------------------------------------------------------
        if fonts_dir is None:
            try:
                from django.conf import settings as django_settings

                fonts_dir = str(django_settings.STATIC_ROOT)
            except Exception:
                fonts_dir = "files/static"

        self._fonts_loaded = self._register_fonts(str(fonts_dir))

        # Police par defaut (noms resolus pour usage interne)
        self._font_body = self.FONT_BODY if self._fonts_loaded else self.FONT_FALLBACK
        self._font_header = self.FONT_HEADER if self._fonts_loaded else self.FONT_FALLBACK

        # Police initiale
        self.set_font(self._font_body, size=FONT_SIZE_DEFAULT)

        # ----------------------------------------------------------------
        # Donnees du footer (remplies via add_footer_content)
        # ----------------------------------------------------------------
        self._footer_email = ""
        self._footer_text = ""

    # ====================================================================
    # Enregistrement des polices
    # ====================================================================
    def _register_fonts(self, fonts_dir):
        """
        Enregistre les polices ClanBook et ClanMedium depuis le repertoire donne.
        Retourne True si au moins la police body a ete chargee, False sinon.

        :param fonts_dir: chemin du repertoire contenant les fichiers .otf
        :return: True si les polices sont disponibles
        """
        loaded = False

        # ClanBook (corps de texte)
        # CSS : font-family:'ClanBook',sans-serif; (table, p)
        clan_book_path = os.path.join(fonts_dir, "ClanBook.otf")
        if os.path.isfile(clan_book_path):
            self.add_font(self.FONT_BODY, "", clan_book_path, uni=True)
            self.add_font(self.FONT_BODY, "B", clan_book_path, uni=True)
            loaded = True

        # ClanMedium (entetes, fournisseur, sousEntete, totaux)
        # CSS : font-family:'ClanMedium', sans-serif; (.entete, .fournisseur, etc.)
        clan_medium_path = os.path.join(fonts_dir, "ClanMedium.otf")
        if os.path.isfile(clan_medium_path):
            self.add_font(self.FONT_HEADER, "", clan_medium_path, uni=True)
            self.add_font(self.FONT_HEADER, "B", clan_medium_path, uni=True)

        # ClanThin (rarement utilise, charge pour completude)
        clan_thin_path = os.path.join(fonts_dir, "ClanThin.otf")
        if os.path.isfile(clan_thin_path):
            self.add_font("ClanThin", "", clan_thin_path, uni=True)

        return loaded

    # ====================================================================
    # Formatage des nombres : "1 234,56"
    # ====================================================================
    @staticmethod
    def format_number(value, decimals=2):
        """
        Formate un nombre au format francais : espace comme separateur de milliers,
        virgule comme separateur decimal.

        Reproduction exacte du filtre Django ``numbers_format`` defini dans
        heron/templatetags/filters_tags.py :

            nombre, centimes, *_ = str(value).split(".")
            centimes += "0" * 99
            for i, value in enumerate(nombre[::-1], 1):
                return_value += value
                if i % 3 == 0: return_value += " "
            return (return_value[::-1] + "," + centimes[:num]).strip()

        Exemples :
            format_number(1234.5)    -> "1 234,50"
            format_number(0)         -> ""
            format_number(None)      -> ""

        :param value: valeur numerique (int, float, Decimal, str)
        :param decimals: nombre de decimales (defaut 2)
        :return: chaine formatee
        """
        if value is None or value == 0:
            return ""

        # Conversion en float puis verification du zero
        try:
            val = float(value)
        except (ValueError, TypeError):
            return ""

        if val == 0:
            return ""

        # Separation partie entiere / decimale (algorithme identique au filtre Django)
        sign = "-" if val < 0 else ""
        val = abs(val)
        int_part = int(val)
        dec_part = round(val - int_part, decimals)

        # Construction de la partie decimale
        dec_str = str(dec_part).split(".")[1] if decimals > 0 else ""
        dec_str = (dec_str + "0" * decimals)[:decimals]

        # Construction de la partie entiere avec separateur de milliers (espace)
        int_str = str(int_part)
        result = ""
        for i, ch in enumerate(int_str[::-1], 1):
            result += ch
            if i % 3 == 0 and i < len(int_str):
                result += " "
        int_str = result[::-1]

        if decimals > 0:
            return f"{sign}{int_str},{dec_str}"
        return f"{sign}{int_str}"

    # ====================================================================
    # Logos : deux logos cote a cote (pdf_generic_entete.html)
    # ====================================================================
    def add_logos(self, logo_heron_path, logo_signboard_path=None):
        """
        Affiche les deux logos en haut de page, cote a cote.

        Reproduit le HTML de pdf_generic_entete.html :
            <tr>
                <td><img src="logo_heron_01.png" style="width:250px;height:auto;"></td>
                <td><img src="logo_enseigne" style="width:250px;height:auto;"></td>
            </tr>

        250px CSS ~ 65mm a 96 DPI (250 * 25.4 / 96 = 66.15, arrondi a 65)

        :param logo_heron_path: chemin vers logo_heron_01.png
        :param logo_signboard_path: chemin vers le logo enseigne (ou None)
        """
        logo_width = 65  # ~250px CSS en mm
        page_width = self.w - self.l_margin - self.r_margin

        logo_y = self.get_y()
        logo_height = 20

        # Logo Heron (toujours present, cote gauche)
        if logo_heron_path and Path(str(logo_heron_path)).is_file():
            self.image(str(logo_heron_path), x=self.l_margin, y=logo_y, w=logo_width)

        # Logo Enseigne (cote droit, position calquee sur le template : 2e <td>)
        if logo_signboard_path and Path(str(logo_signboard_path)).is_file():
            self.image(
                str(logo_signboard_path),
                x=self.l_margin + page_width / 2,
                y=logo_y,
                w=logo_width,
            )

        # Avancer sous les logos (~20mm hauteur estimee + 4mm espace)
        self.set_y(logo_y + logo_height + 4)

    # ====================================================================
    # Adresses : livre a / facture a (pdf_generic_entete.html)
    # ====================================================================
    def add_addresses(self, invoice):
        """
        Affiche les blocs d'adresses "Livre a" et "Facture a" cote a cote.

        Reproduit le HTML de pdf_generic_entete.html :
            <td style="width:60%;vertical-align: top;">Livre a :
                <p>name_cct</p>
                <p>immeuble_cct</p>
                <p>adresse_cct</p>
                <p>code_postal_cct ville_cct</p>
                <p>pays_cct</p>
                <p>N TVA Intra. : vat_cee_number_cct</p>
            </td>
            <td style="width:40%;vertical-align: top;">Facture a :
                ...memes champs pour third_party...
            </td>

        :param invoice: objet SaleInvoice
        """
        self.set_font(self._font_body, "", FONT_SIZE_DEFAULT)
        parties = invoice.parties

        page_width = self.w - self.l_margin - self.r_margin
        col_left_w = page_width * 0.60
        col_right_w = page_width * 0.40
        line_h = LINE_HEIGHT_ROW

        y_before = self.get_y()

        # ---- Colonne gauche : Livre a ----
        x_left = self.l_margin
        self.set_xy(x_left, y_before)
        self.cell(
            col_left_w, line_h, "Livr\u00e9 \u00e0 :",
            new_x="LMARGIN", new_y="NEXT",
        )

        for text in self._address_lines_cct(parties):
            self.set_x(x_left)
            self.cell(
                col_left_w, line_h, text,
                new_x="LMARGIN", new_y="NEXT",
            )

        y_after_left = self.get_y()

        # ---- Colonne droite : Facture a ----
        x_right = self.l_margin + col_left_w
        self.set_xy(x_right, y_before)
        self.cell(
            col_right_w, line_h, "Factur\u00e9 \u00e0 :",
            new_x="LMARGIN", new_y="NEXT",
        )

        for text in self._address_lines_third_party(parties):
            self.set_xy(x_right, self.get_y())
            self.cell(
                col_right_w, line_h, text,
                new_x="LMARGIN", new_y="NEXT",
            )

        y_after_right = self.get_y()

        # Positionner apres le plus grand des deux blocs
        self.set_y(max(y_after_left, y_after_right) + 2)

    def _address_lines_cct(self, parties):
        """
        Retourne les lignes d'adresse CCT (Livre a).
        Reproduit les champs de PartiesInvoices pour la partie CCT.
        """
        lines = []
        if parties:
            for attr in ["name_cct", "immeuble_cct", "adresse_cct"]:
                val = getattr(parties, attr, None)
                if val:
                    lines.append(str(val))

            cp = getattr(parties, "code_postal_cct", "") or ""
            ville = getattr(parties, "ville_cct", "") or ""
            if cp or ville:
                lines.append(f"{cp} {ville}".strip())

            pays = getattr(parties, "pays_cct", None)
            if pays:
                lines.append(str(pays))

            vat = getattr(parties, "vat_cee_number_cct", None)
            if vat:
                lines.append(f"N\u00b0 TVA Intra. : {vat}")

        return lines

    def _address_lines_third_party(self, parties):
        """
        Retourne les lignes d'adresse du tiers (Facture a).
        Reproduit les champs de PartiesInvoices pour la partie third_party.
        """
        lines = []
        if parties:
            for attr in ["name_third_party", "immeuble_third_party", "adresse_third_party"]:
                val = getattr(parties, attr, None)
                if val:
                    lines.append(str(val))

            cp = getattr(parties, "code_postal_third_party", "") or ""
            ville = getattr(parties, "ville_third_party", "") or ""
            if cp or ville:
                lines.append(f"{cp} {ville}".strip())

            pays = getattr(parties, "pays_third_party", None)
            if pays:
                lines.append(str(pays))

            vat = getattr(parties, "vat_cee_number_client", None)
            if vat:
                lines.append(f"N\u00b0 TVA Intra. : {vat}")

        return lines

    # ====================================================================
    # Metadonnees facture (pdf_generic_entete.html - table interne)
    # ====================================================================
    def add_invoice_meta(self, invoice, formation=False):
        """
        Affiche les metadonnees de la facture.

        Reproduit le HTML de pdf_generic_entete.html :
            <table>
                {% if formation %}
                    <tr><td>N Adherent Forco</td><td> : {{ centers.member_num }}</td></tr>
                {% endif %}
                <tr><td>Code Centrale</td><td> : {{ code_center }}</td></tr>
                <tr><td>N Compte client</td><td> : {{ third_party_num }}</td></tr>
                <tr><td>N CCT X3</td><td> : {{ cct }}</td></tr>
                <tr><td>Date facture</td><td> : {{ invoice_date|date:"d/m/Y" }}</td></tr>
                <tr><td style="color:red;font-weight:bold;">Devise</td>
                    <td style="color:red;font-weight:bold;"> : Euro</td></tr>
            </table>

        :param invoice: objet SaleInvoice
        :param formation: True si facture de formation (affiche N Adherent Forco)
        """
        self.set_font(self._font_body, "", FONT_SIZE_DEFAULT)
        label_w = 40  # ~95px CSS converti en mm
        val_w = 60
        line_h = LINE_HEIGHT_ROW

        meta_lines = []

        # N Adherent Forco (conditionnel, uniquement pour les formations)
        if formation:
            member_num = ""
            if invoice.centers and hasattr(invoice.centers, "member_num"):
                member_num = str(invoice.centers.member_num or "")
            meta_lines.append(("N\u00b0 Adh\u00e9rent Forco", member_num))

        meta_lines.extend(
            [
                ("Code Centrale", str(invoice.code_center or "")),
                (
                    "N\u00b0 Compte client",
                    str(invoice.third_party_num.third_party_num),
                ),
                ("N\u00b0 CCT X3", str(invoice.cct)),
                (
                    "Date facture",
                    (
                        invoice.invoice_date.strftime("%d/%m/%Y")
                        if invoice.invoice_date
                        else ""
                    ),
                ),
            ]
        )

        self.set_font(self._font_body, "", FONT_SIZE_DEFAULT)
        for label, value in meta_lines:
            self.set_x(self.l_margin)
            self.cell(label_w, line_h, label)
            self.cell(
                val_w, line_h, f": {value}",
                new_x="LMARGIN", new_y="NEXT",
            )

        # Devise en rouge et gras (CSS : color: red; font-weight: bold;)
        self.set_x(self.l_margin)
        self.set_text_color(*COLOR_RED)
        self.set_font(self._font_header, "", FONT_SIZE_DEFAULT)
        self.cell(label_w, line_h, "Devise")
        self.cell(
            val_w, line_h, ": Euro",
            new_x="LMARGIN", new_y="NEXT",
        )

        # Reinitialiser la couleur et la police
        self.set_text_color(*COLOR_BLACK)
        self.set_font(self._font_body, "", FONT_SIZE_DEFAULT)
        self.ln(2)

    # ====================================================================
    # Entete complete (logos + adresses + meta) - raccourci
    # ====================================================================
    def draw_entete(self, invoice=None, logo_heron=None, logo_signboard=None,
                    formation=False):
        """
        Dessine l'entete complete de la facture (logos + adresses + meta).
        Raccourci qui appelle add_logos, add_addresses et add_invoice_meta.

        Peut etre appele sans argument (utilise self.invoice, self.logo_heron,
        self.logo_signboard) ou avec des arguments explicites.

        :param invoice: objet SaleInvoice (defaut self.invoice)
        :param logo_heron: chemin vers logo_heron_01.png (defaut self.logo_heron)
        :param logo_signboard: chemin vers le logo enseigne (defaut self.logo_signboard)
        :param formation: True si facture de formation
        """
        inv = invoice or self.invoice
        lh = logo_heron or self.logo_heron
        ls = logo_signboard or self.logo_signboard
        self.add_logos(lh, ls)
        self.add_addresses(inv)
        self.add_invoice_meta(inv, formation=formation)

    # ====================================================================
    # Ligne d'entete noire (classe CSS .entete)
    # ====================================================================
    def add_entete_row(self, texts, widths, h=None, aligns=None, bg_color=None):
        """
        Dessine une ligne d'entete avec fond noir et texte blanc (classe CSS .entete).

        Comme fpdf2 ne supporte pas border-radius, on utilise un rectangle plein noir.
        Le rendu visuel reste fidele.

        CSS reproduit :
            .entete {
                background-color: black;
                color: white;
                font-family: 'ClanMedium', sans-serif;
            }
            .entete td:first-child {
                border-top-left-radius: 14px;   /* non reproduit - pas de support fpdf2 */
                border-bottom-left-radius: 14px;
                padding-left: 5px;
            }
            tr.entete > td { padding: 5px; }

        :param texts: liste de textes pour chaque cellule
        :param widths: liste de largeurs (en mm) pour chaque cellule
        :param h: hauteur de la ligne (defaut LINE_HEIGHT_HEADER = 6mm)
        :param aligns: liste d'alignements ("L", "C", "R") par cellule
        :param bg_color: tuple (R, G, B) pour surcharger le fond
                         (ex: COLOR_DARK_HEADER pour les lignes TVA)
        """
        if h is None:
            h = LINE_HEIGHT_HEADER

        if aligns is None:
            aligns = ["L"] * len(texts)

        fill_color = bg_color or COLOR_BLACK
        total_width = sum(widths)

        # Fond arrondi (reproduit border-radius: 14px ~ 4mm)
        x_start = self.get_x()
        y_start = self.get_y()
        self._draw_rounded_bg(x_start, y_start, total_width, h, 4, fill_color)

        # Texte par-dessus le fond arrondi
        self.set_xy(x_start, y_start)
        self.set_text_color(*COLOR_WHITE)
        self.set_font(self._font_header, "", FONT_SIZE_DEFAULT)

        for i, (text, width, align) in enumerate(zip(texts, widths, aligns)):
            display_text = f" {text}" if i == 0 else str(text)
            self.cell(width, h, display_text, border=0, align=align)

        self.ln(h)

        # Reinitialiser les couleurs
        self.set_text_color(*COLOR_BLACK)
        self.set_fill_color(*COLOR_WHITE)
        self.set_font(self._font_body, "", FONT_SIZE_DEFAULT)

    # ====================================================================
    # Ligne de donnees (classe CSS tr.lignes)
    # ====================================================================
    def add_data_row(self, texts, widths, aligns, h=None, bold_indices=None):
        """
        Dessine une ligne de donnees avec bordures grises laterales.

        CSS reproduit :
            table, p {
                font-family: 'ClanBook', sans-serif;
                font-size: 11px;
            }
            tr.lignes > td {
                padding: 2px 5px;
                border-left: 1px solid #dadada;
                border-right: 1px solid #dadada;
            }
            tr.lignes > td:first-child, tr.lignes > td:last-child {
                border-left: none;
                border-right: none;
            }

        :param texts: liste de textes pour chaque cellule
        :param widths: liste de largeurs (en mm) pour chaque cellule
        :param aligns: liste d'alignements ("L", "C", "R") par cellule
        :param h: hauteur de la ligne (defaut LINE_HEIGHT_ROW = 5mm)
        :param bold_indices: set/liste d'indices de colonnes a mettre en gras
                             (pour les lignes {% ifchanged %} avec <strong>)
        """
        if h is None:
            h = LINE_HEIGHT_ROW

        if bold_indices is None:
            bold_indices = set()
        else:
            bold_indices = set(bold_indices)

        self.set_draw_color(*COLOR_GRAY_BORDER)

        for i, (text, width, align) in enumerate(zip(texts, widths, aligns)):
            # Bordures laterales sauf premiere et derniere cellule
            is_first = i == 0
            is_last = i == len(texts) - 1

            if is_first or is_last:
                border = 0
            else:
                border = "LR"

            if i in bold_indices:
                self.set_font(self._font_body, "B", FONT_SIZE_DEFAULT)
            else:
                self.set_font(self._font_body, "", FONT_SIZE_DEFAULT)

            self.cell(width, h, f" {text}", border=border, align=align)

        self.ln(h)

        # Reinitialiser
        self.set_draw_color(*COLOR_BLACK)
        self.set_font(self._font_body, "", FONT_SIZE_DEFAULT)

    # ====================================================================
    # Titre de page centre dans un bandeau noir
    # ====================================================================
    def add_page_title(self, title):
        """
        Affiche un titre centre dans un bandeau noir pleine largeur.

        Reproduit le HTML :
            <tr class="entete">
                <td style="text-align: center; font-size: 1.1em; padding: 5px 5px;">
                    FACTURE N 000xxx
                </td>
            </tr>

        :param title: texte du titre (ex: "Facture N 000012345")
        """
        page_width = self.w - self.l_margin - self.r_margin

        # Fond arrondi (reproduit border-radius: 14px ~ 4mm)
        x_start = self.get_x()
        y_start = self.get_y()
        self._draw_rounded_bg(x_start, y_start, page_width, LINE_HEIGHT_HEADER, 4, COLOR_BLACK)

        # Texte par-dessus
        self.set_xy(x_start, y_start)
        self.set_text_color(*COLOR_WHITE)
        self.set_font(self._font_header, "B", FONT_SIZE_TITLE)

        self.cell(
            page_width,
            LINE_HEIGHT_HEADER,
            title,
            align="C",
            new_x="LMARGIN",
            new_y="NEXT",
        )

        # Reinitialiser
        self.set_text_color(*COLOR_BLACK)
        self.set_fill_color(*COLOR_WHITE)
        self.set_font(self._font_body, "", FONT_SIZE_DEFAULT)
        self.ln(2)

    # ====================================================================
    # Footer : email + hr + mentions legales + page/total_pages
    # ====================================================================
    def add_footer_content(self, email_contact, footer_text):
        """
        Enregistre les donnees du footer pour qu'elles soient utilisees
        par la methode footer() appelee automatiquement par fpdf2.

        Reproduit pdf_generic_footer_invoices.html :
            <div class="footer">
                <p style="text-align:center;">
                    Email de contact pour tout renseignement
                    sur cette facturation : <strong>{{ signboard.email_contact }}</strong>
                </p>
                <hr>
                <p style="font-size:0.2em;">{{ centers.footer }}</p>
            </div>

        Et general_style_counter_pages.html :
            @bottom-right {
                content: counter(page) "/" counter(pages);
                font-size: 11px;
            }

        :param email_contact: adresse email de contact (signboard.email_contact)
        :param footer_text: texte des mentions legales (centers.footer)
        """
        self._footer_email = email_contact or ""
        self._footer_text = footer_text or ""

    def footer(self):
        """
        Methode appelee automatiquement par fpdf2 en bas de chaque page.

        Dessine dans l'ordre :
        1. Le texte d'email de contact centre (CSS : text-align:center)
        2. Un trait horizontal (hr CSS)
        3. Le texte des mentions legales en tres petit (CSS : font-size:0.2em)
        4. Le numero de page "page/total" en bas a droite
           (CSS : @bottom-right { content: counter(page) "/" counter(pages); })
        """
        page_width = self.w - self.l_margin - self.r_margin

        # Position a 15mm du bas de page
        self.set_y(-15)

        # 1. Email de contact
        if self._footer_email:
            self.set_font(self._font_body, "", FONT_SIZE_FOOTER)
            self.set_text_color(*COLOR_BLACK)
            email_text = (
                "Email de contact pour tout renseignement sur cette facturation"
                f" : {self._footer_email}"
            )
            self.cell(page_width, LINE_HEIGHT_FOOTER, email_text, align="C")
            self.ln(LINE_HEIGHT_FOOTER)

            # 2. Trait horizontal (hr)
            self.set_draw_color(*COLOR_BLACK)
            y_hr = self.get_y()
            self.line(self.l_margin, y_hr, self.w - self.r_margin, y_hr)
            self.ln(1)

        # 3. Mentions legales (font-size: 0.2em dans le CSS)
        if self._footer_text:
            self.set_font(self._font_body, "", FONT_SIZE_FOOTER_SMALL)
            self.set_text_color(*COLOR_BLACK)
            self.multi_cell(page_width, 2, self._footer_text, align="L")

        # 4. Numero de page (en bas a droite)
        # Reproduit : content: counter(page) "/" counter(pages); font-size: 11px;
        self.set_font(self._font_body, "", FONT_SIZE_DEFAULT)
        self.set_text_color(*COLOR_BLACK)
        self.set_y(-8)
        self.cell(
            page_width,
            LINE_HEIGHT_FOOTER,
            f"{self.page_no()}/{{nb}}",
            align="R",
        )

    # ====================================================================
    # Methodes de compatibilite et variantes d'appel
    # ====================================================================

    def draw_title_banner(self, text):
        """
        Dessine une banniere de titre avec fond noir et texte blanc centre.
        Alias de add_page_title pour compatibilite.

        :param text: texte du titre
        """
        self.add_page_title(text)

    def draw_paiement(self, invoice=None):
        """Alias de add_paiement. Utilise self.invoice si non fourni."""
        self.add_paiement(invoice)

    def draw_mentions_legales(self, invoice=None):
        """Alias de add_mentions_legales. Utilise self.invoice si non fourni."""
        self.add_mentions_legales(invoice)

    def draw_table_header(self, columns, fill_color=None):
        """
        Dessine une ligne d'en-tete de tableau avec coins arrondis.

        :param columns: liste de tuples (texte, largeur_mm, alignement)
        :param fill_color: tuple (R, G, B), defaut COLOR_BLACK
        """
        if fill_color is None:
            fill_color = COLOR_BLACK

        total_width = sum(w for _, w, _ in columns)

        # Fond arrondi (reproduit border-radius: 14px ~ 4mm)
        x_start = self.get_x()
        y_start = self.get_y()
        self._draw_rounded_bg(x_start, y_start, total_width, LINE_HEIGHT_HEADER, 4, fill_color)

        # Texte par-dessus
        self.set_xy(x_start, y_start)
        self.set_text_color(*COLOR_WHITE)
        self.set_font(self._font_header, "", FONT_SIZE_DEFAULT)
        for text, w, align in columns:
            self.cell(w, LINE_HEIGHT_HEADER, text, align=align)
        self.ln()
        self.set_text_color(*COLOR_BLACK)
        self.set_fill_color(*COLOR_WHITE)
        self.set_font(self._font_body, size=FONT_SIZE_DEFAULT)

    def draw_data_row(self, cells):
        """
        Dessine une ligne de donnees standard.

        :param cells: liste de tuples (texte, largeur_mm, alignement)
        """
        self.set_font(self._font_body, size=FONT_SIZE_DEFAULT)
        for text, w, align in cells:
            self.cell(w, LINE_HEIGHT_ROW, str(text), align=align)
        self.ln()

    def add_table_header_row(self, columns, col_widths, aligns, fill_color=None):
        """
        Dessine une ligne d'en-tete de tableau (format liste separees).

        :param columns: liste de textes
        :param col_widths: liste de largeurs en mm
        :param aligns: liste d'alignements ("L", "C", "R")
        :param fill_color: tuple (R, G, B), defaut COLOR_BLACK
        """
        if fill_color is None:
            fill_color = COLOR_BLACK
        self.set_fill_color(*fill_color)
        self.set_text_color(*COLOR_WHITE)
        self.set_font(self._font_header, "B", FONT_SIZE_DEFAULT)
        for text, w, align in zip(columns, col_widths, aligns):
            self.cell(w, LINE_HEIGHT_HEADER, text, align=align, fill=True)
        self.ln()
        self.set_text_color(*COLOR_BLACK)
        self.set_font(self._font_body, "", FONT_SIZE_DEFAULT)

    def draw_footer_block(self, invoice=None):
        """
        Dessine le bloc footer directement depuis un objet invoice.
        Alternative a add_footer_content + footer() pour un placement manuel.

        Reproduit pdf_generic_footer_invoices.html.

        :param invoice: objet SaleInvoice (defaut self.invoice)
        """
        inv = invoice or self.invoice
        page_width = self.w - self.l_margin - self.r_margin
        email = inv.signboard.email_contact or ""

        self.set_font(self._font_body, size=FONT_SIZE_DEFAULT)
        self.cell(
            page_width,
            LINE_HEIGHT_ROW,
            (
                "Email de contact pour tout renseignement "
                f"sur cette facturation : {email}"
            ),
            align="C",
            new_x="LMARGIN",
            new_y="NEXT",
        )

        # Ligne horizontale
        y = self.get_y()
        self.line(self.l_margin, y, self.l_margin + page_width, y)
        self.ln(1)

        # Footer center text (mentions legales)
        footer_text = inv.centers.footer or ""
        if footer_text:
            self.set_font(self._font_body, size=FONT_SIZE_FOOTER_SMALL)
            self.multi_cell(
                page_width, 2, footer_text,
                align="C", new_x="LMARGIN", new_y="NEXT",
            )
            self.set_font(self._font_body, size=FONT_SIZE_DEFAULT)

    # ====================================================================
    # Paiement (pdf_generic_paiement.html)
    # ====================================================================
    def add_paiement(self, invoice=None):
        """
        Affiche le mode de paiement et la date d'echeance.
        Reproduit pdf_generic_paiement.html.

        :param invoice: objet SaleInvoice (defaut self.invoice)
        """
        invoice = invoice or self.invoice
        self.set_font(self._font_header, "", FONT_SIZE_DEFAULT)
        self.cell(30, LINE_HEIGHT_ROW, "Mode de paiement", new_x="END")
        self.set_font(self._font_body, size=FONT_SIZE_DEFAULT)
        payment = invoice.parties.payment_condition_client or ""
        self.cell(
            0, LINE_HEIGHT_ROW, f" : {payment}",
            new_x="LMARGIN", new_y="NEXT",
        )

        if invoice.date_echeance:
            self.set_font(self._font_header, "", FONT_SIZE_DEFAULT)
            self.cell(18, LINE_HEIGHT_ROW, "\u00c9ch\u00e9ance", new_x="END")
            self.set_font(self._font_body, size=FONT_SIZE_DEFAULT)
            self.cell(
                0,
                LINE_HEIGHT_ROW,
                f" : {invoice.date_echeance.strftime('%d/%m/%Y')}",
                new_x="LMARGIN",
                new_y="NEXT",
            )
        self.ln(2)

    # ====================================================================
    # Mentions legales (pdf_generic_mentions_legales.html)
    # ====================================================================
    def add_mentions_legales(self, invoice=None):
        """
        Affiche les mentions legales en petite police.
        Reproduit pdf_generic_mentions_legales.html.

        CSS reproduit :
            .mentionsLegales { font-size: 0.6em; }

        :param invoice: objet SaleInvoice (defaut self.invoice)
        """
        invoice = invoice or self.invoice
        legal = invoice.centers.legal_notice_center or ""
        if legal:
            self.set_font(self._font_body, size=FONT_SIZE_FOOTER)
            self.multi_cell(
                0, LINE_HEIGHT_FOOTER - 1, legal,
                new_x="LMARGIN", new_y="NEXT",
            )
            self.set_font(self._font_body, size=FONT_SIZE_DEFAULT)
            self.ln(2)

    # ====================================================================
    # Footer complet depuis l'objet invoice (add_footer_block)
    # ====================================================================
    def add_footer_block(self, invoice=None):
        """
        Affiche le footer : email contact + hr + texte centre.
        Reproduit pdf_generic_footer_invoices.html.

        :param invoice: objet SaleInvoice (defaut self.invoice)
        """
        invoice = invoice or self.invoice
        page_width = self.w - self.l_margin - self.r_margin
        email = invoice.signboard.email_contact or ""

        self.set_font(self._font_body, size=FONT_SIZE_DEFAULT)
        self.cell(
            page_width,
            LINE_HEIGHT_ROW,
            (
                "Email de contact pour tout renseignement "
                f"sur cette facturation : {email}"
            ),
            align="C",
            new_x="LMARGIN",
            new_y="NEXT",
        )

        # Ligne horizontale
        y = self.get_y()
        self.line(self.l_margin, y, self.l_margin + page_width, y)
        self.ln(1)

        # Footer center text
        footer_text = invoice.centers.footer or ""
        if footer_text:
            self.set_font(self._font_body, size=FONT_SIZE_FOOTER_SMALL)
            self.multi_cell(
                page_width, 2, footer_text,
                align="C", new_x="LMARGIN", new_y="NEXT",
            )
            self.set_font(self._font_body, size=FONT_SIZE_DEFAULT)

    # ====================================================================
    # Styles specifiques aux pages de details et recapitulatifs
    # ====================================================================

    def add_supplier_row(self, text, h=None):
        """
        Dessine une ligne de nom de fournisseur avec fond gris moyen.

        CSS reproduit (general_style_details.html) :
            .fournisseur {
                text-align: center;
                font-size: 1.2em;
                background-color: #dbdbdb;
                color: black;
                text-transform: uppercase;
                font-family: 'ClanMedium', sans-serif;
                border: 1px solid #d4d4d4;
            }

        :param text: nom du fournisseur
        :param h: hauteur de la ligne (defaut LINE_HEIGHT_HEADER)
        """
        if h is None:
            h = LINE_HEIGHT_HEADER

        page_width = self.w - self.l_margin - self.r_margin

        self.set_fill_color(*COLOR_GRAY_MEDIUM)
        self.set_text_color(*COLOR_BLACK)
        self.set_draw_color(212, 212, 212)  # #d4d4d4
        self.set_font(self._font_header, "", FONT_SIZE_SUPPLIER_NAME)

        self.cell(
            page_width,
            h,
            text.upper(),
            border=1,
            align="C",
            fill=True,
        )
        self.ln(h)

        # Reinitialiser
        self.set_text_color(*COLOR_BLACK)
        self.set_fill_color(*COLOR_WHITE)
        self.set_draw_color(*COLOR_BLACK)
        self.set_font(self._font_body, "", FONT_SIZE_DEFAULT)

    def add_sub_header_row(self, texts, widths, h=None, aligns=None):
        """
        Dessine une ligne de sous-entete avec fond gris clair.

        CSS reproduit (general_style_details.html) :
            .sousEntete {
                background-color: #ededed;
                color: black;
                font-family: 'ClanMedium', sans-serif;
                text-transform: uppercase;
                text-align: center;
                font-size: 0.9em;
            }
            .sousEntete > td { border: 1px solid #d4d4d4; }

        :param texts: liste de textes
        :param widths: liste de largeurs (en mm)
        :param h: hauteur de la ligne (defaut LINE_HEIGHT_HEADER)
        :param aligns: liste d'alignements (defaut "C" pour toutes)
        """
        if h is None:
            h = LINE_HEIGHT_HEADER

        if aligns is None:
            aligns = ["C"] * len(texts)

        self.set_fill_color(*COLOR_GRAY_LIGHT)
        self.set_text_color(*COLOR_BLACK)
        self.set_draw_color(212, 212, 212)  # #d4d4d4
        self.set_font(self._font_header, "", FONT_SIZE_SUB_ENTRY)

        for text, width, align in zip(texts, widths, aligns):
            display = text.upper() if isinstance(text, str) else str(text)
            self.cell(width, h, display, border=1, align=align, fill=True)

        self.ln(h)

        # Reinitialiser
        self.set_text_color(*COLOR_BLACK)
        self.set_fill_color(*COLOR_WHITE)
        self.set_draw_color(*COLOR_BLACK)
        self.set_font(self._font_body, "", FONT_SIZE_DEFAULT)

    def add_sub_total_row(self, texts, widths, aligns=None, h=None):
        """
        Dessine une ligne de sous-total avec fond gris moyen.

        CSS reproduit :
            .sousTotaux > TD {
                background: #dbdbdb;
                font-size: 0.8em;
                font-weight: bold;
                color: black;
                padding: 3px 5px 3px 0;
            }

        :param texts: liste de textes
        :param widths: liste de largeurs (en mm)
        :param aligns: liste d'alignements (defaut "R" pour toutes)
        :param h: hauteur de la ligne
        """
        if h is None:
            h = LINE_HEIGHT_ROW

        if aligns is None:
            aligns = ["R"] * len(texts)

        self.set_fill_color(*COLOR_GRAY_MEDIUM)
        self.set_text_color(*COLOR_BLACK)
        self.set_font(self._font_header, "B", FONT_SIZE_SUB_TOTAL)

        for text, width, align in zip(texts, widths, aligns):
            self.cell(width, h, str(text), border=0, align=align, fill=True)

        self.ln(h)

        # Reinitialiser
        self.set_fill_color(*COLOR_WHITE)
        self.set_font(self._font_body, "", FONT_SIZE_DEFAULT)

    def add_total_row(self, texts, widths, aligns=None, h=None):
        """
        Dessine une ligne de total avec fond gris fonce.

        CSS reproduit :
            .totaux > TD {
                background-color: #bebdbd;
                font-family: 'ClanMedium', sans-serif;
                font-size: 0.8em;
                font-weight: bold;
                color: black;
            }

        :param texts: liste de textes
        :param widths: liste de largeurs (en mm)
        :param aligns: liste d'alignements (defaut "R" pour toutes)
        :param h: hauteur de la ligne
        """
        if h is None:
            h = LINE_HEIGHT_ROW

        if aligns is None:
            aligns = ["R"] * len(texts)

        self.set_fill_color(*COLOR_GRAY_DARK)
        self.set_text_color(*COLOR_BLACK)
        self.set_font(self._font_header, "B", FONT_SIZE_SUB_TOTAL)

        for text, width, align in zip(texts, widths, aligns):
            self.cell(width, h, str(text), border=0, align=align, fill=True)

        self.ln(h)

        # Reinitialiser
        self.set_fill_color(*COLOR_WHITE)
        self.set_font(self._font_body, "", FONT_SIZE_DEFAULT)

    def add_bordered_row(self, texts, widths, aligns, h=None, fill_color=None):
        """
        Dessine une ligne avec bordures grises completes sur chaque cellule.

        CSS reproduit (general_style_details.html, general_style_sub_details.html) :
            tr.bordures > td {
                border: 1px solid #dadada;
            }
            tr.bordures > td:first-child, tr.bordures > td:last-child {
                border-left: none;
                border-right: none;
            }

        :param texts: liste de textes
        :param widths: liste de largeurs (en mm)
        :param aligns: liste d'alignements
        :param h: hauteur de la ligne
        :param fill_color: tuple (R, G, B) pour le fond (None = sans fond)
        """
        if h is None:
            h = LINE_HEIGHT_ROW

        self.set_draw_color(*COLOR_GRAY_BORDER)
        self.set_font(self._font_body, "", FONT_SIZE_DEFAULT)

        if fill_color:
            self.set_fill_color(*fill_color)

        for i, (text, width, align) in enumerate(zip(texts, widths, aligns)):
            is_first = i == 0
            is_last = i == len(texts) - 1

            if is_first or is_last:
                border = "TB"
            else:
                border = 1

            self.cell(
                width,
                h,
                f" {text}",
                border=border,
                align=align,
                fill=bool(fill_color),
            )

        self.ln(h)

        # Reinitialiser
        self.set_draw_color(*COLOR_BLACK)
        if fill_color:
            self.set_fill_color(*COLOR_WHITE)

    def add_bl_row(self, texts, widths, aligns=None, h=None):
        """
        Dessine une ligne de BL avec fond gris tres clair.

        CSS reproduit (general_style_sub_details.html) :
            .borduresBL td {
                background: #f5f5f5;
                font-family: 'ClanMedium', sans-serif;
                padding-top: 5px;
            }

        :param texts: liste de textes
        :param widths: liste de largeurs (en mm)
        :param aligns: liste d'alignements
        :param h: hauteur de la ligne
        """
        if h is None:
            h = LINE_HEIGHT_ROW

        if aligns is None:
            aligns = ["L"] + ["R"] * (len(texts) - 1)

        self.set_fill_color(*COLOR_GRAY_BG_BL)
        self.set_text_color(*COLOR_BLACK)
        self.set_font(self._font_header, "", FONT_SIZE_DEFAULT)

        for text, width, align in zip(texts, widths, aligns):
            self.cell(width, h, str(text), border=0, align=align, fill=True)

        self.ln(h)

        # Reinitialiser
        self.set_fill_color(*COLOR_WHITE)
        self.set_font(self._font_body, "", FONT_SIZE_DEFAULT)

    def add_group_row(self, text, h=None):
        """
        Dessine une ligne de groupe centree avec police agrandie.

        CSS reproduit (general_style_details.html) :
            .groupe { text-align: center; font-size: 1.2em; padding: 5px; }

        :param text: texte du groupe
        :param h: hauteur de la ligne
        """
        if h is None:
            h = LINE_HEIGHT_HEADER

        page_width = self.w - self.l_margin - self.r_margin

        self.set_font(self._font_body, "", FONT_SIZE_SUPPLIER_NAME)
        self.set_text_color(*COLOR_BLACK)

        self.cell(page_width, h, text, align="C")
        self.ln(h)

        self.set_font(self._font_body, "", FONT_SIZE_DEFAULT)

    # ====================================================================
    # Utilitaires
    # ====================================================================
    def _draw_rounded_bg(self, x, y, w, h, _r, fill_color):
        """
        Dessine un rectangle plein en arriere-plan pour les lignes d'entete.

        Note : fpdf2 ne gere pas correctement les coins arrondis via ses
        methodes internes. On utilise un rectangle simple, visuellement
        suffisant pour les factures.

        :param x: position X
        :param y: position Y
        :param w: largeur totale
        :param h: hauteur
        :param _r: rayon ignore (conserve pour compatibilite d'appel)
        :param fill_color: tuple (R, G, B)
        """
        self.set_fill_color(*fill_color)
        self.set_draw_color(*fill_color)
        self.rect(x, y, w, h, "F")
        self.set_draw_color(*COLOR_BLACK)

    def add_vertical_space(self, mm=5):
        """Ajoute un espace vertical de la hauteur specifiee en mm."""
        self.ln(mm)