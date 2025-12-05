# pylint: disable=
"""
FR : Settings pour la création à la vollée des répertoires des factures founisseurs
EN : Settings for on-the-fly creation of supplier invoice directories

Commentaire:

created at: 2022-04-09
created by: Paulo ALVES

modified at: 2022-04-09
modified by: Paulo ALVES
"""
from pathlib import Path
from heron.utils.directories import lazy_mkdir

# ==================================================================================================
# REPERTOIRES DES FICHIERS A IMPORTER
# ==================================================================================================

# REPERTOIRE PROCESSING POUR IMPORT FICHIERS FROUNISSEURS
PROCESS_DIR = lazy_mkdir("files/processing/suppliers_invoices_files")

# REPERTOIRE IMPORT FICHIERS BBGR_BULK
BBGR_BULK = lazy_mkdir("files/processing/suppliers_invoices_files/BBGR_BULK")

# REPERTOIRE IMPORT FICHIERS COSIUM
COSIUM = lazy_mkdir("files/processing/suppliers_invoices_files/COSIUM")

# REPERTOIRE IMPORT FICHIERS COSIUM ACHATS SEULS
COSIUM_ACHATS = lazy_mkdir("files/processing/suppliers_invoices_files/COSIUM_ACHATS")

# REPERTOIRE IMPORT FICHIERS BBGR_MONTHLY
BBGR_MONTHLY = lazy_mkdir("files/processing/suppliers_invoices_files/BBGR_MONTHLY")

# REPERTOIRE IMPORT FICHIERS BBGR_RETOURS
BBGR_RETOURS = lazy_mkdir("files/processing/suppliers_invoices_files/BBGR_RETOURS")

# REPERTOIRE IMPORT FICHIERS BBGR_STATMENT
BBGR_STATMENT = lazy_mkdir("files/processing/suppliers_invoices_files/BBGR_STATMENT")

# REPERTOIRE IMPORT FICHIERS EDI
EDI = lazy_mkdir("files/processing/suppliers_invoices_files/EDI")

# REPERTOIRE IMPORT FICHIERS EYE_CONFORT
EYE_CONFORT = lazy_mkdir("files/processing/suppliers_invoices_files/EYE_CONFORT")

# REPERTOIRE IMPORT FICHIERS GENERIQUE
GENERIQUE = lazy_mkdir("files/processing/suppliers_invoices_files/GENERIQUE")

# REPERTOIRE IMPORT FICHIERS GENERIQUE INTERNAL (Factures internes)
GENERIQUE_INTERNAL = lazy_mkdir("files/processing/suppliers_invoices_files/GENERIQUE_INTERNAL")

# REPERTOIRE IMPORT FICHIERS HANSATON
HANSATON = lazy_mkdir("files/processing/suppliers_invoices_files/HANSATON")

# REPERTOIRE IMPORT FICHIERS HEARING
HEARING = lazy_mkdir("files/processing/suppliers_invoices_files/HEARING")

# REPERTOIRE IMPORT FICHIERS INTERSON
INTERSON = lazy_mkdir("files/processing/suppliers_invoices_files/INTERSON")

# REPERTOIRE IMPORT FICHIERS JOHNSON
JOHNSON = lazy_mkdir("files/processing/suppliers_invoices_files/JOHNSON")

# REPERTOIRE IMPORT FICHIERS LMC
LMC = lazy_mkdir("files/processing/suppliers_invoices_files/LMC")

# REPERTOIRE IMPORT FICHIERS NEWSON
NEWSON = lazy_mkdir("files/processing/suppliers_invoices_files/NEWSON")

# REPERTOIRE IMPORT FICHIERS PHONAK
PHONAK = lazy_mkdir("files/processing/suppliers_invoices_files/PHONAK")

# REPERTOIRE POST PROCESSING FICHIERS EDI
POST_PROCESSING = lazy_mkdir("files/processing/suppliers_invoices_files/POST_PROCESSING")

# REPERTOIRE PRE PROCESSING FICHIERS EDI
PRE_PROCESSING = lazy_mkdir("files/processing/suppliers_invoices_files/PRE_PROCESSING")

# REPERTOIRE IMPORT FICHIERS PRODITION
PRODITION = lazy_mkdir("files/processing/suppliers_invoices_files/PRODITION")

# REPERTOIRE IMPORT FICHIERS SIGNIA
SIGNIA = lazy_mkdir("files/processing/suppliers_invoices_files/SIGNIA")

# REPERTOIRE IMPORT FICHIERS STARKEY
STARKEY = lazy_mkdir("files/processing/suppliers_invoices_files/STARKEY")

# REPERTOIRE IMPORT FICHIERS TECHNIDIS
TECHNIDIS = lazy_mkdir("files/processing/suppliers_invoices_files/TECHNIDIS")

# REPERTOIRE IMPORT FICHIERS TRANSFERTS
TRANSFERTS = lazy_mkdir("files/processing/suppliers_invoices_files/TRANSFERTS")

# REPERTOIRE IMPORT FICHIERS UNITRON
UNITRON = lazy_mkdir("files/processing/suppliers_invoices_files/UNITRON")

# REPERTOIRE IMPORT FICHIERS WIDEX
WIDEX = lazy_mkdir("files/processing/suppliers_invoices_files/WIDEX")

# REPERTOIRE IMPORT FICHIERS WSAU
WSAU = lazy_mkdir("files/processing/suppliers_invoices_files/WSAU")

# REPERTOIRE IMPORT FICHIERS WIDEX_GA
WIDEX_GA = lazy_mkdir("files/processing/suppliers_invoices_files/WIDEX_GA")

# REPERTOIRE IMPORT FICHIERS REQUETE SQL SAGE SUR AXE BU REFAC_0
SAGE_YOOZ_REFAC0 = lazy_mkdir("files/processing/suppliers_invoices_files/SAGE_YOOZ_REFAC0")

# REPERTOIRE IMPORT FICHIERS AXE PRO / ARTICLES / COMPTES
IMPORT_ACCOUNTS = lazy_mkdir("files/processing/suppliers_invoices_files/IMPORT_ACCOUNTS")

# ==================================================================================================
# BACKUP DE DEPLACEMENT DES FICHIERS IMPORTES
# ==================================================================================================

# REPERTOIRE DES BACKUP FACTURES FOURNISSEURS
BACKUP_SUPPLIERS_DIR = lazy_mkdir("files/backup/suppliers_invoices_files")

# REPERTOIRE BACKUP DES IMPORTS DES ARTICLES SANS COMPTES
BACKUP_WITHOUT_ACCOUNT_DIR = lazy_mkdir("files/backup/suppliers_invoices_files/ARTICLES_SANS_COMPTES")

# REPERTOIRE BACKUP DES IMPORTS DES ABONNEMENTS PAR MAISON
BACKUP_CLIENS_SUBSCRIPTION_DIR = lazy_mkdir("files/backup/suppliers_invoices_files/ABONNEMENTS_PAR_MAISONS")

# REPERTOIRE BACKUP FICHIERS BBGR_BULK
BACKUP_BBGR_BULK = lazy_mkdir("files/backup/suppliers_invoices_files/BBGR_BULK")

# REPERTOIRE IMPORT FICHIERS COSIUM
BACKUP_COSIUM = lazy_mkdir("files/backup/suppliers_invoices_files/COSIUM")

# REPERTOIRE IMPORT FICHIERS COSIUM ACHATS
BACKUP_COSIUM_ACHATS = lazy_mkdir("files/backup/suppliers_invoices_files/COSIUM_ACHATS")

# REPERTOIRE BACKUP FICHIERS BBGR_MONTHLY
BACKUP_BBGR_MONTHLY = lazy_mkdir("files/backup/suppliers_invoices_files/BBGR_MONTHLY")

# REPERTOIRE BACKUP FICHIERS BBGR_RETOURS
BACKUP_BBGR_RETOURS = lazy_mkdir("files/backup/suppliers_invoices_files/BBGR_RETOURS")

# REPERTOIRE BACKUP FICHIERS BBGR_STATMENT
BACKUP_BBGR_STATMENT = lazy_mkdir("files/backup/suppliers_invoices_files/BBGR_STATMENT")

# REPERTOIRE BACKUP FICHIERS EDI
BACKUP_EDI = lazy_mkdir("files/backup/suppliers_invoices_files/EDI")

# REPERTOIRE BACKUP FICHIERS EYE_CONFORT
BACKUP_EYE_CONFORT = lazy_mkdir("files/backup/suppliers_invoices_files/EYE_CONFORT")

# REPERTOIRE BACKUP FICHIERS GENERIQUE
BACKUP_GENERIQUE = lazy_mkdir("files/backup/suppliers_invoices_files/GENERIQUE")

# REPERTOIRE BACKUP FICHIERS  GENERIQUE INTERNAL (Factures internes)
BACKUP_GENERIQUE_INTERNAL = lazy_mkdir("files/backup/suppliers_invoices_files/GENERIQUE_INTERNAL")

# REPERTOIRE BACKUP FICHIERS HANSATON
BACKUP_HANSATON = lazy_mkdir("files/backup/suppliers_invoices_files/HANSATON")

# REPERTOIRE BACKUP FICHIERS HEARING
BACKUP_HEARING = lazy_mkdir("files/backup/suppliers_invoices_files/HEARING")

# REPERTOIRE BACKUP FICHIERS INTERSON
BACKUP_INTERSON = lazy_mkdir("files/backup/suppliers_invoices_files/INTERSON")

# REPERTOIRE BACKUP FICHIERS JOHNSON
BACKUP_JOHNSON = lazy_mkdir("files/backup/suppliers_invoices_files/JOHNSON")

# REPERTOIRE BACKUP FICHIERS LMC
BACKUP_LMC = lazy_mkdir("files/backup/suppliers_invoices_files/LMC")

# REPERTOIRE BACKUP FICHIERS NEWSON
BACKUP_NEWSON = lazy_mkdir("files/backup/suppliers_invoices_files/NEWSON")

# REPERTOIRE BACKUP FICHIERS PHONAK
BACKUP_PHONAK = lazy_mkdir("files/backup/suppliers_invoices_files/PHONAK")

# REPERTOIRE BACKUP FICHIERS PRODITION
BACKUP_PRODITION = lazy_mkdir("files/backup/suppliers_invoices_files/PRODITION")

# REPERTOIRE BACKUP FICHIERS SIGNIA
BACKUP_SIGNIA = lazy_mkdir("files/backup/suppliers_invoices_files/SIGNIA")

# REPERTOIRE BACKUP FICHIERS STARKEY
BACKUP_STARKEY = lazy_mkdir("files/backup/suppliers_invoices_files/STARKEY")

# REPERTOIRE BACKUP FICHIERS TECHNIDIS
BACKUP_TECHNIDIS = lazy_mkdir("files/backup/suppliers_invoices_files/TECHNIDIS")

# REPERTOIRE BACKUP FICHIERS TRANSFERTS
BACKUP_TRANSFERTS = lazy_mkdir("files/backup/suppliers_invoices_files/TRANSFERTS")

# REPERTOIRE BACKUP FICHIERS UNITRON
BACKUP_UNITRON = lazy_mkdir("files/backup/suppliers_invoices_files/UNITRON")

# REPERTOIRE BACKUP FICHIERS WIDEX
BACKUP_WSAU = lazy_mkdir("files/backup/suppliers_invoices_files/WSAU")

# REPERTOIRE BACKUP FICHIERS WIDEX
BACKUP_WIDEX = lazy_mkdir("files/backup/suppliers_invoices_files/WIDEX")

# REPERTOIRE BACKUP FICHIERS WIDEX_GA
BACKUP_WIDEX_GA = lazy_mkdir("files/backup/suppliers_invoices_files/WIDEX_GA")

# REPERTOIRE BACKUP FICHIERS REQUETE SQL SAGE SUR AXE BU REFAC_0
BACKUP_SAGE_YOOZ_REFAC0 = lazy_mkdir("files/backup/suppliers_invoices_files/SAGE_YOOZ_REFAC0")

# REPERTOIRE BACKUP FICHIERS AXE PRO / ARTICLES / COMPTES
BACKUP_IMPORT_ACCOUNTS = lazy_mkdir("files/backup/suppliers_invoices_files/IMPORT_ACCOUNTS")
