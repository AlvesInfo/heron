"""Module d'export du fichier excel pour les Contrôles de Refacturation.

Commentaire:

created at: 2026-02-16
created by: Paulo ALVES

modified at: 2026-02-16
modified by: Paulo ALVES
"""

import io

from apps.core.excel_outputs.excel_writer import (
    f_entetes,
    f_ligne,
)
from apps.core.excel_outputs.generic_list_export import excel_list_export
from apps.parameters.models import ControlRebilling

columns_list_control_rebilling = [
    {
        "entete": "Contrôle",
        "f_entete": {
            **f_entetes,
            "bg_color": "#CCC0DA",
        },
        "f_ligne": {
            **f_ligne,
            "align": "left",
        },
        "width": 20,
    },
    {
        "entete": "Commentaire",
        "f_entete": {
            **f_entetes,
            "bg_color": "#CCC0DA",
        },
        "f_ligne": {
            **f_ligne,
            "align": "left",
        },
        "width": 80,
    },
]


def get_row():
    """Class qui renvoie les bonnes colonnes pour le fichier Excel."""
    yield from [
        (
            row.name,
            row.comment or "",
        )
        for row in ControlRebilling.objects.all()
    ]


def excel_liste_control_rebilling(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier de liste des Controles de Refacturation."""
    titre_list = file_name.split("_")
    titre = " ".join(titre_list[:-4])
    columns = columns_list_control_rebilling

    return excel_list_export(
        file_io,
        file_name,
        sheet_name=titre[:30],
        title=titre,
        columns=columns,
        rows=get_row(),
        header_row=4,
    )
