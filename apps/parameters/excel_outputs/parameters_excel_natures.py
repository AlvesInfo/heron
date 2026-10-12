"""Module d'export du fichier excel pour les Numérotations.

Commentaire:

created at: 2023-03-12
created by: Paulo ALVES

modified at: 2023-03-12
modified by: Paulo ALVES
"""

import io

from apps.core.excel_outputs.generic_list_export import excel_list_export
from apps.parameters.excel_outputs.output_excel_filles_columns import columns_list_nature
from apps.parameters.models import Nature


def get_row():
    """Class qui renvoie les bonnes colonnes pour le fichier Excel."""
    yield from [
        (
            row.get("name"),
            row.get("to_display"),
            "X" if row.get("for_contact") else "",
            "X" if row.get("for_personnel") else "",
            "X" if row.get("for_formation") else "",
        )
        for row in Nature.objects.all()
        .values(
            "name",
            "to_display",
            "for_contact",
            "for_personnel",
            "for_formation",
        )
        .order_by("name")
    ]


def excel_liste_natures(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier de liste des Natures/Genres."""
    titre_list = file_name.split("_")
    titre = " ".join(titre_list[:-4])
    columns = columns_list_nature

    return excel_list_export(
        file_io,
        file_name,
        sheet_name=titre[:30],
        title=titre,
        columns=columns,
        rows=get_row(),
        orientation="landscape",
    )
