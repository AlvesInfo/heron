"""Module d'export du fichier excel pour des axe rfa à prendre

Commentaire:

created at: 2024-08-09
created by: Paulo ALVES

modified at: 2024-08-09
modified by: Paulo ALVES
"""

import io

from apps.core.excel_outputs.excel_writer import (
    f_entetes,
    f_ligne,
)
from apps.rfa.models import SectionRfa
from apps.core.excel_outputs.generic_list_export import excel_list_export


columns_list = [
    {
        "entete": "Section",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#DCE7F5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "center",
            },
        },
        "width": 11,
    },
    {
        "entete": "Intitulé",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#DCE7F5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "center",
            },
        },
        "width": 25,
    },
]


def get_row():
    """Class qui renvoie les bonnes colonnes pour le fichier Excel"""

    yield from [
        (
            row.get("axe_rfa__section"),
            row.get("axe_rfa__name"),
        )
        for row in SectionRfa.objects.all()
        .order_by("axe_rfa__section")
        .values(
            "axe_rfa__section",
            "axe_rfa__name",
        )
        .order_by("axe_rfa__section")
    ]


def excel_list_rfa_sections(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier de liste des sections rfa à prendre pour les RFA"""
    titre_list = file_name.split("_")
    titre = " ".join(titre_list[:-4])
    columns = columns_list

    return excel_list_export(
        file_io,
        file_name,
        sheet_name=titre[:30],
        title=titre,
        columns=columns,
        rows=get_row(),
        header_row=4,
        odd_color="#F2F2F2",
        odd_first=True,
    )
