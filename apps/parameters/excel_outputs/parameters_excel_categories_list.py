"""Module d'export du fichier excel pour les Catégories.

Commentaire:

created at: 2022-05-12
created by: Paulo ALVES

modified at: 2022-05-12
modified by: Paulo ALVES
"""

import io

from apps.core.excel_outputs.generic_list_export import excel_list_export
from apps.parameters.excel_outputs.output_excel_filles_columns import columns_list_categories
from apps.parameters.models import Category


def get_row():
    """Class qui renvoie les bonnes colonnes pour le fichier Excel."""
    yield from [
        (
            row.get("ranking"),
            row.get("code"),
            row.get("name"),
            row.get("big_sub_category__ranking") or "",
            row.get("big_sub_category__code") or "",
            row.get("big_sub_category__name") or "",
        )
        for row in Category.objects.all()
        .order_by("ranking", "big_sub_category__code")
        .values(
            "ranking",
            "code",
            "name",
            "big_sub_category__ranking",
            "big_sub_category__code",
            "big_sub_category__name",
        )
        .order_by("ranking", "big_sub_category__ranking")
    ]


def excel_liste_categories(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier de liste des Catégories."""
    titre_list = file_name.split("_")
    titre = " ".join(titre_list[:-4])
    columns = columns_list_categories

    return excel_list_export(
        file_io,
        file_name,
        sheet_name=titre[:30],
        title=titre,
        columns=columns,
        rows=get_row(),
        header_row=4,
        merged_headers=[
            (0, 2, "Grande Catégorie", columns[0].get("f_entete")),
            (3, 5, "Rubrique Prestation associée", columns[3].get("f_entete")),
        ],
    )
