"""Module d'export des familles client.

Commentaire:

created at: 2026-02-14
created by: Paulo ALVES

modified at: 2026-02-14
modified by: Paulo ALVES
"""

import io

from apps.centers_clients.models import ClientFamilly
from apps.core.excel_outputs.excel_writer import (
    f_entetes,
    f_ligne,
)
from apps.core.excel_outputs.generic_list_export import excel_list_export

columns = [
    {
        "entete": "Catégore",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "center",
        },
        "width": 20,
    },
    {
        "entete": "Commentaire",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "center",
        },
        "width": 80,
    },
]


def get_clean_rows():
    """Retourne les lignes à écrire."""
    return [(str(row.name), str(row.comment or "")) for row in ClientFamilly.objects.all()]


def excel_client_familly(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier de liste Familles Clients."""
    return excel_list_export(
        file_io,
        file_name,
        sheet_name="LISTE CATEGORIES CLIENTS",
        title="LISTE DES CATEGORIES CLIENTS",
        columns=columns,
        rows=get_clean_rows(),
    )
