"""Module d'export du fichier de la liste des couples Tiers / Masions à exlucre de la facturation.

Commentaire:

created at: 2023-01-21
created by: Paulo ALVES

modified at: 2023-01-21
modified by: Paulo ALVES
"""

import io

from apps.centers_clients.models import MaisonSupllierExclusion
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
        "entete": "CLIENT",
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
        (str(row.third_party_num), str(row.cct_uuid_identification))
        for row in MaisonSupllierExclusion.objects.all()
    ]


def excel_liste_exclusion(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier de liste exclusions Tiers X3/Clients."""
    return excel_list_export(
        file_io,
        file_name,
        sheet_name="LISTE DES EXCLUSIONS",
        title="LISTE DES EXCLUSIONS TIERS X3/CLIENTS",
        columns=columns,
        rows=get_clean_rows(),
    )
