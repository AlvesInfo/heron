"""Module d'export du fichier excel pour les exclusion des rfa des clients

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
from apps.rfa.models import ClientExclusion
from apps.core.excel_outputs.generic_list_export import excel_list_export


columns_list = [
    {
        "entete": "Client/CCT",
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
            row.get("cct__cct"),
            row.get("cct__intitule"),
        )
        for row in ClientExclusion.objects.all()
        .order_by("cct__cct")
        .values(
            "cct__cct",
            "cct__intitule",
        )
        .order_by("cct__cct")
    ]


def excel_list_rfa_clients_exclusion(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier de liste des Clients/CCT à exclure des RFA"""
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
