"""Module d'export du fichier excel pour les Numérotations

Commentaire:

created at: 2023-03-12
created by: Paulo ALVES

modified at: 2023-03-12
modified by: Paulo ALVES
"""

import io

from apps.parameters.models import Counter
from apps.parameters.excel_outputs.output_excel_filles_columns import columns_list_numberings
from apps.core.excel_outputs.generic_list_export import excel_list_export


def get_row():
    """Class qui renvoie les bonnes colonnes pour le fichier Excel"""

    yield from [
        (
            row.get("name"),
            row.get("function", ""),
            row.get("prefix", ""),
            row.get("suffix", ""),
            row.get("lpad_num", ""),
            row.get("separateur", ""),
            row.get("description", ""),
        )
        for row in Counter.objects.all()
        .values(
            "name",
            "function",
            "prefix",
            "suffix",
            "lpad_num",
            "separateur",
            "description",
        )
        .order_by("name")
    ]


def excel_liste_numberings(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier de liste des Numérotation"""
    titre_list = file_name.split("_")
    titre = " ".join(titre_list[:-4])
    columns = columns_list_numberings

    return excel_list_export(
        file_io,
        file_name,
        sheet_name=titre[:30],
        title=titre,
        columns=columns,
        rows=get_row(),
        orientation="landscape",
    )
