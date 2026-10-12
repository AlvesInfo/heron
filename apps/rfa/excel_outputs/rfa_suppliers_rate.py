"""Module d'export du fichier excel des taux de RFA par founisseurs

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
from apps.rfa.models import SupplierRate
from apps.core.excel_outputs.generic_list_export import excel_list_export


columns_list = [
    {
        "entete": "Code Tiers",
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
        "entete": "Nom Tiers",
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
    {
        "entete": "Taux RFA",
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
                "num_format": "#,##0.00",
            },
        },
        "width": 10,
    },
]


def get_row():
    """Class qui renvoie les bonnes colonnes pour le fichier Excel"""

    yield from [
        (
            row.get("supplier__third_party_num"),
            row.get("supplier__name"),
            row.get("rfa_rate"),
        )
        for row in SupplierRate.objects.all()
        .order_by("supplier__third_party_num")
        .values(
            "supplier__third_party_num",
            "supplier__name",
            "rfa_rate",
        )
        .order_by("supplier__third_party_num")
    ]


def excel_list_suppliers_rate(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier de liste des taux de RFA par founisseurs"""
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
