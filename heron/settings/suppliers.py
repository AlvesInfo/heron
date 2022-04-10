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

# REPERTOIRE PROCESSING POUR IMPORT FICHIERS FROUNISSEURS

PROCESS_DIR = (
        Path(__file__).parent.parent.parent / "files/processing/suppliers_invoices_files"
).resolve()
Path.mkdir(PROCESS_DIR, exist_ok=True)

# REPERTOIRE DES BACKUP FACTURES FOURNISSEURS
BACKUP_SUPPLIERS_DIR = (
        Path(__file__).parent.parent.parent / "files/backup/suppliers_invoices_files"
).resolve()
Path.mkdir(BACKUP_SUPPLIERS_DIR, exist_ok=True)

# REPERTOIRE IMPORT FICHIERS NEWSON
NEWSON = (Path(PROCESS_DIR) / "NEWSON").resolve()
Path.mkdir(NEWSON, exist_ok=True)

# REPERTOIRE IMPORT FICHIERS STARKEY
STARKEY = (Path(PROCESS_DIR) / "STARKEY").resolve()
Path.mkdir(STARKEY, exist_ok=True)

# REPERTOIRE IMPORT FICHIERS PRODITION
PRODITION = (Path(PROCESS_DIR) / "PRODITION").resolve()
Path.mkdir(PRODITION, exist_ok=True)

# REPERTOIRE IMPORT FICHIERS TECHNIDIS
TECHNIDIS = (Path(PROCESS_DIR) / "TECHNIDIS").resolve()
Path.mkdir(TECHNIDIS, exist_ok=True)

# REPERTOIRE IMPORT FICHIERS BBRG_BULK
BBRG_BULK = (Path(PROCESS_DIR) / "BBRG_BULK").resolve()
Path.mkdir(BBRG_BULK, exist_ok=True)

# REPERTOIRE IMPORT FICHIERS PHONAK
PHONAK = (Path(PROCESS_DIR) / "PHONAK").resolve()
Path.mkdir(PHONAK, exist_ok=True)

# REPERTOIRE IMPORT FICHIERS INTERSON
INTERSON = (Path(PROCESS_DIR) / "INTERSON").resolve()
Path.mkdir(INTERSON, exist_ok=True)

# REPERTOIRE IMPORT FICHIERS UNITRON
UNITRON = (Path(PROCESS_DIR) / "UNITRON").resolve()
Path.mkdir(UNITRON, exist_ok=True)

# REPERTOIRE IMPORT FICHIERS JOHNSON
JOHNSON = (Path(PROCESS_DIR) / "JOHNSON").resolve()
Path.mkdir(JOHNSON, exist_ok=True)

# REPERTOIRE IMPORT FICHIERS WIDEX
WIDEX = (Path(PROCESS_DIR) / "WIDEX").resolve()
Path.mkdir(WIDEX, exist_ok=True)

# REPERTOIRE IMPORT FICHIERS WIDEX_GA
WIDEX_GA = (Path(PROCESS_DIR) / "WIDEX_GA").resolve()
Path.mkdir(WIDEX_GA, exist_ok=True)

# REPERTOIRE IMPORT FICHIERS LMC
LMC = (Path(PROCESS_DIR) / "LMC").resolve()
Path.mkdir(LMC, exist_ok=True)

# REPERTOIRE IMPORT FICHIERS EYE_CONFORT
EYE_CONFORT = (Path(PROCESS_DIR) / "EYE_CONFORT").resolve()
Path.mkdir(EYE_CONFORT, exist_ok=True)

# REPERTOIRE IMPORT FICHIERS SIGNIA
SIGNIA = (Path(PROCESS_DIR) / "SIGNIA").resolve()
Path.mkdir(SIGNIA, exist_ok=True)

# REPERTOIRE IMPORT FICHIERS HEARING
HEARING = (Path(PROCESS_DIR) / "HEARING").resolve()
Path.mkdir(HEARING, exist_ok=True)

# REPERTOIRE IMPORT FICHIERS GENERIQUE
GENERIQUE = (Path(PROCESS_DIR) / "GENERIQUE").resolve()
Path.mkdir(GENERIQUE, exist_ok=True)

# REPERTOIRE IMPORT FICHIERS EDI
EDI = (Path(PROCESS_DIR) / "EDI").resolve()
Path.mkdir(EDI, exist_ok=True)

# REPERTOIRE PRE PROCESSING FICHIERS EDI
PRE_PROCESSING = (Path(PROCESS_DIR) / "PRE_PROCESSING").resolve()
Path.mkdir(PRE_PROCESSING, exist_ok=True)

# REPERTOIRE POST PROCESSING FICHIERS EDI
POST_PROCESSING = (Path(PROCESS_DIR) / "POST_PROCESSING").resolve()
Path.mkdir(POST_PROCESSING, exist_ok=True)
