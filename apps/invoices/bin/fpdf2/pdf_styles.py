# pylint: disable=E0401,C0413
"""
FR : Styles et constantes de mise en forme PDF reproduisant le CSS des templates HTML
EN : PDF styling constants reproducing the CSS from HTML templates

Commentaire:
    Reproduction fidèle des styles définis dans :
    - general_style_invoices.html (header, suppliers, page portrait A4)
    - general_style_details.html (details, page paysage A4)
    - general_style_sub_details.html (sub_details, page portrait A4)

created at: 2024-02-10
created by: Paulo ALVES

modified at: 2024-02-10
modified by: Paulo ALVES
"""

# =============================================================================
# COULEURS (R, G, B)
# =============================================================================
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_GRAY_LIGHT = (237, 237, 237)       # #ededed
COLOR_GRAY_MEDIUM = (219, 219, 219)      # #dbdbdb
COLOR_GRAY_DARK = (190, 189, 189)        # #bebdbd
COLOR_GRAY_BORDER = (218, 218, 218)      # #dadada
COLOR_GRAY_BG_BL = (245, 245, 245)      # #f5f5f5
COLOR_DARK_HEADER = (64, 64, 64)         # #404040
COLOR_RED = (255, 0, 0)

# =============================================================================
# TAILLES DE POLICE (en pt)
# =============================================================================
FONT_SIZE_DEFAULT = 8          # ~11px converti en pt pour fpdf2
FONT_SIZE_SMALL = 7            # ~9px (details paysage)
FONT_SIZE_TITLE = 9            # ~1.1em relatif au default
FONT_SIZE_SUPPLIER_NAME = 9    # ~1.2em relatif au small
FONT_SIZE_FOOTER = 5           # ~0.6em mentions légales
FONT_SIZE_FOOTER_SMALL = 3     # ~0.2em footer center
FONT_SIZE_SUB_TOTAL = 6.5      # ~0.8em sous-totaux
FONT_SIZE_SUB_ENTRY = 7        # ~0.9em sous-entetes

# =============================================================================
# MARGES DE PAGE (en mm) - correspondant à @page CSS
# =============================================================================
# Portrait (header, suppliers, sub_details) : margin 10mm
MARGIN_PORTRAIT = 10

# Paysage (details) : margin 0 0 5mm 0
MARGIN_LANDSCAPE_TOP = 0
MARGIN_LANDSCAPE_BOTTOM = 5
MARGIN_LANDSCAPE_LEFT = 0
MARGIN_LANDSCAPE_RIGHT = 0

# =============================================================================
# HAUTEURS DE LIGNES (en mm)
# =============================================================================
LINE_HEIGHT_HEADER = 6       # lignes d'entête
LINE_HEIGHT_ROW = 5          # lignes de données
LINE_HEIGHT_SMALL = 4        # lignes compactes (details)
LINE_HEIGHT_FOOTER = 4       # footer

# =============================================================================
# PADDING INTERNE (en mm)
# =============================================================================
CELL_PADDING = 1
CELL_PADDING_LEFT = 2
CELL_PADDING_RIGHT = 2