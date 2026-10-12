"""Module d'export du fichier excel de la liste des Regroupements de facturation.

Commentaire:

created at: 2023-01-21
created by: Paulo ALVES

modified at: 2023-01-21
modified by: Paulo ALVES
"""

import io

from apps.centers_purchasing.models import GroupingGoods
from apps.core.excel_outputs.excel_writer import (
    f_entetes,
    f_ligne,
)
from apps.core.excel_outputs.generic_list_export import excel_list_export

columns = [
    {
        "entete": "Ranking",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "center",
        },
        "width": 8,
    },
    {
        "entete": "Base",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "center",
        },
        "width": 25,
    },
    {
        "entete": "Regroupement",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "center",
        },
        "width": 25,
    },
]


def get_clean_rows():
    """Fonction qui renvoie les éléments pour le fichier Excel."""
    return [
        (
            str(row.ranking),
            str(row.base),
            str(row.grouping_goods),
        )
        for row in GroupingGoods.objects.all()
    ]


def excel_liste_grouping_goods(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier de la liste des Regroupements de facturation."""
    titre_list = file_name.split("_")
    titre = " ".join(titre_list[:-4])

    return excel_list_export(
        file_io,
        file_name,
        sheet_name="REGROUPEMENT DE FACTURATION",
        title=titre,
        columns=columns,
        rows=get_clean_rows(),
        orientation="landscape",
    )
