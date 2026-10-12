"""Module d'export du fichier excel pour Familles Statistiques/Axes

Commentaire:

created at: 2022-05-12
created by: Paulo ALVES

modified at: 2022-05-12
modified by: Paulo ALVES
"""

import io

from apps.book.models.supplier_identifiers_models import StatFamillyAxes
from apps.book.excel_outputs.book_columns import columns_list_statistiques
from apps.core.excel_outputs.generic_list_export import excel_list_export


def get_row():
    """Class qui renvoie les bonnes colonnes pour le fichier Excel"""

    yield from [
        (
            row.get("name"),
            row.get("description"),
            "X" if row.get("regex_bool") else "",
            row.get("stat_axes__invoice_column"),
            row.get("stat_axes__regex_match") or "",
            row.get("stat_axes__expected_result") or "",
            row.get("stat_axes__axe_pro__section") or "",
            row.get("stat_axes__description") or "",
            row.get("stat_axes__norme") or "",
            row.get("stat_axes__comment") or "",
            row.get("stat_axes__big_category__name") or "",
            row.get("stat_axes__sub_category__name") or "",
            row.get("stat_axes__item_weight") or "",
            row.get("stat_axes__unit_weight") or "",
            row.get("stat_axes__customs_code") or "",
        )
        for row in StatFamillyAxes.objects.all()
        .values(
            "name",
            "description",
            "regex_bool",
            "stat_axes__invoice_column",
            "stat_axes__regex_match",
            "stat_axes__expected_result",
            "stat_axes__axe_pro__section",
            "stat_axes__description",
            "stat_axes__norme",
            "stat_axes__comment",
            "stat_axes__big_category__name",
            "stat_axes__sub_category__name",
            "stat_axes__item_weight",
            "stat_axes__unit_weight",
            "stat_axes__customs_code",
        )
        .order_by("name", "stat_axes__invoice_column", "stat_axes__regex_match")
    ]


def excel_liste_statistiques(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier de liste des Familles Statistiques/Axes"""
    titre_list = file_name.split("_")
    titre = " ".join(titre_list[:-4])
    columns = columns_list_statistiques

    return excel_list_export(
        file_io,
        file_name,
        sheet_name=titre[:30],
        title=titre,
        columns=columns,
        rows=get_row(),
        header_row=4,
        merged_headers=[(0, 2, 'Familles', columns[0].get('f_entete')), (3, 14, 'Statistiques/Axes', columns[3].get('f_entete'))],
    )
