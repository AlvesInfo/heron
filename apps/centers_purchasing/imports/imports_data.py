# pylint: disable=W0703,W1203
"""
FR : Module d'import des données des parametres ou data de remplissage de tables
EN : Parameter data import module or table filling data

Commentaire:

created at: 2023-05-13
created by: Paulo ALVES

modified at: 2023-05-13
modified by: Paulo ALVES
"""
import uuid
from pathlib import Path

from django.utils import timezone

from apps.core.functions.functions_setups import settings
from apps.data_flux.trace import get_trace
from apps.core.bin.import_files import import_file_process
from apps.centers_purchasing.forms.forms_djantic.forms_data import (
    AxeProAccountSchema,
)
from apps.centers_purchasing.bin.data_pre_processing_pool import (
    translate_accounts_axe_pro_category,
)
from apps.centers_purchasing.bin.data_post_processing_pool import (
    post_axe_pro_account,
)
from apps.centers_purchasing.models import AccountsAxeProCategory

proccessing_dir = Path(settings.PROCESSING_SAGE_DIR)


def axe_pro_account():
    """Import du fichier des Axes pro / catégories / comptes"""
    params_dict = {
        "model": AccountsAxeProCategory,
        "validator": AxeProAccountSchema,
        "trace_name": "Import Axe_pro/account",
        "application_name": "import_accounts_axe_pro_category",
        "flow_name": "import_accounts_axe_pro_category",
        "comment": "",
        "add_fields_dict": {
            "uuid_identification": (uuid.uuid4, {}),
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
        "translate_file": translate_accounts_axe_pro_category,
        "pre_processing": None,
        "post_processing": post_axe_pro_account,
    }
    import_file_process(
        files_dir=settings.IMPORT_ACCOUNTS,
        params_dict=params_dict,
        save_dir=settings.BACKUP_IMPORT_ACCOUNTS,
    )
