"""Module d'export du fichier excel pour les Functions.

Commentaire:

created at: 2023-02-23
created by: Paulo ALVES

modified at: 2023-02-23
modified by: Paulo ALVES
"""

import io

from apps.core.excel_outputs.generic_list_export import excel_list_export
from apps.parameters.excel_outputs.output_excel_filles_columns import columns_list_functions
from apps.parameters.models import InvoiceFunctions


def get_row():
    """Class qui renvoie les bonnes colonnes pour le fichier Excel."""
    yield from [
        (
            row.get("function_name"),
            row.get("function"),
            row.get("absolute_path_windows") or "",
            row.get("absolute_path_linux") or "",
            row.get("description") or "",
        )
        for row in InvoiceFunctions.objects.all()
        .values(
            "function_name",
            "function",
            "absolute_path_windows",
            "absolute_path_linux",
            "description",
        )
        .order_by("function_name")
    ]


def excel_liste_functions(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier de liste des Functions."""
    titre_list = file_name.split("_")
    titre = " ".join(titre_list[:-4])
    columns = columns_list_functions

    return excel_list_export(
        file_io,
        file_name,
        sheet_name=titre[:30],
        title=titre,
        columns=columns,
        rows=get_row(),
        orientation="landscape",
    )
