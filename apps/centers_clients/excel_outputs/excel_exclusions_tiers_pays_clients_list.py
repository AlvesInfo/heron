"""Module d'export du fichier3de1l21liste des couples Tiers/Pays Masions à exlucre de la facturation.

Commentaire:

created at: 2023-01-21
created by: Paulo ALVES

modified at: 2023-01-21
modified by: Paulo ALVES
"""

import io

from apps.centers_clients.models import SupllierCountryExclusion
from apps.core.excel_outputs.excel_writer import (
    f_entetes,
    f_ligne,
)
from apps.core.excel_outputs.generic_list_export import excel_list_export

columns = [
    {
        "entete": "TIERS X3",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "center",
        },
        "width": 50,
    },
    {
        "entete": "PAYS CLIENTS",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "center",
        },
        "width": 50,
    },
]


def get_clean_rows():
    """Retourne les lignes à écrire."""
    return [
        (str(row.third_party_num), str(row.pays)) for row in SupllierCountryExclusion.objects.all()
    ]


def excel_liste_exclusion_pays(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier de liste exclusions Tiers X3/Pays Clients."""
    return excel_list_export(
        file_io,
        file_name,
        sheet_name="LISTE DES EXCLUSIONS TIERS PAYS",
        title="LISTE DES EXCLUSIONS TIERS X3/PAYS CLIENTS",
        columns=columns,
        rows=get_clean_rows(),
    )
