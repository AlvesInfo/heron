"""Module d'export du fichier excel Dictionnaire Axe Pro/Regroupement de facturation

Commentaire:

created at: 2023-01-21
created by: Paulo ALVES

modified at: 2023-01-21
modified by: Paulo ALVES
"""

import io

from apps.core.excel_outputs.excel_writer import (
    f_entetes,
    f_ligne,
)
from apps.centers_purchasing.models import AxeProGroupingGoods
from apps.core.excel_outputs.generic_list_export import excel_list_export

columns = [
    {
        "entete": "Axe PRO",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "center",
            },
        },
        "width": 35,
    },
    {
        "entete": "Regroupement",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "center",
            },
        },
        "width": 65,
    },
]


def get_clean_rows():
    """Fonction qui renvoie les éléments pour le fichier Excel"""

    return [
        (
            str(row.axe_pro),
            str(row.grouping_goods),
        )
        for row in AxeProGroupingGoods.objects.all()
    ]


def excel_liste_axe_grouping(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier Dictionnaire Axe Pro/Regroupement de facturation"""
    titre_list = file_name.split("_")
    titre = " ".join(titre_list[:-4])

    return excel_list_export(
        file_io,
        file_name,
        sheet_name='AXE PRO VS REGROUPEMENT FAC',
        title=titre,
        columns=columns,
        rows=get_clean_rows(),
        orientation="landscape",
    )
