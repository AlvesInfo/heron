# pylint: disable=E0401
"""
FR : Tables de correspondance entre les données heron (codes X3) et le modèle
     de facture attendu par le serveur Factur-X (facturx-fr)
EN : Mapping tables between heron data (X3 codes) and the invoice model
     expected by the Factur-X server (facturx-fr)

Commentaire:

created at: 2026-10-10
created by: Paulo ALVES

modified at: 2026-10-10
modified by: Paulo ALVES
"""

# Type de facture heron -> code UNTDID 1001 (BT-3)
INVOICE_TYPE_CODES = {
    "FAC": "380",  # Facture
    "AVC": "381",  # Avoir
}

# Catégorie de l'opération (mention obligatoire sept. 2026) selon la grande catégorie
# heron. Les catégories absentes sont considérées comme des prestations de services.
OPERATION_CATEGORIES = {
    "marchandises": "delivery",
    "materiel": "delivery",
}
DEFAULT_OPERATION_CATEGORY = "service"

# Régime de TVA X3 (accountancy_vatsage.vat_regime) -> catégorie TVA EN16931 (BT-151)
# pour les lignes à taux 0 : (catégorie, code motif BT-120, motif BT-121)
ZERO_RATE_VAT_CATEGORIES = {
    "CEE": (
        "K",
        "VATEX-EU-IC",
        "Livraison intracommunautaire exonérée - Art. 262 ter I du CGI",
    ),
    "EXP": ("G", "VATEX-EU-G", "Exportation hors UE exonérée - Art. 262 I du CGI"),
    "DOM": ("E", None, "Exonération de TVA - DOM"),
    "FRA": ("E", None, "Exonération de TVA"),
}
DEFAULT_ZERO_RATE_VAT_CATEGORY = ("E", None, "Exonération de TVA")

# Unité heron (parameters_unitchoices.num) -> code UN/ECE Rec. 20 accepté par facturx-fr
UNIT_CODES = {
    1: "C62",  # U
    2: "C62",  # Grammes (pas de code supporté, unité par défaut)
    3: "KGM",  # Kg
    4: "XPP",  # Pièce
    5: "C62",  # Boite
    6: "C62",  # Carton
    7: "DAY",  # Jrs
    8: "MON",  # Mois
    9: "C62",  # Forfait
    10: "HUR",  # Heures
    11: "SET",  # Ens
    12: "C62",  # %
}
DEFAULT_UNIT_CODE = "C62"

# Mode de règlement X3 (accountancy_modereglement.code / name) -> code UNTDID 4461 (BT-81)
# Recherche par mot-clé (insensible à la casse) dans le code puis l'intitulé.
PAYMENT_MEANS_KEYWORDS = (
    ("PRLV", "59"),  # Prélèvement SEPA
    ("PRE", "59"),
    ("VIR", "58"),  # Virement SEPA
    ("CHQ", "20"),  # Chèque
    ("CHE", "20"),
    ("CB", "48"),  # Carte bancaire
    ("CAR", "48"),
    ("ESP", "10"),  # Espèces
    ("LCR", "30"),  # Lettre de change : virement générique
    ("TRA", "30"),
)
DEFAULT_PAYMENT_MEANS_CODE = "58"

# Pays considéré comme domestique
DOMESTIC_COUNTRY_CODE = "FR"
