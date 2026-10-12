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
from apps.centers_purchasing.models import ApplicableProVat
from apps.core.excel_outputs.generic_list_export import excel_list_export

columns = [
    {
        "entete": "Centrale Fille",
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
        "entete": "Axe Pro",
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
        "entete": "TVA",
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
        "width": 15,
    },
]


def get_clean_rows():
    """Fonction qui renvoie les éléments pour le fichier Excel"""

    return [
        (
            str(row.child_center),
            str(row.axe_pro),
            str(row.vat),
        )
        for row in ApplicableProVat.objects.all()
    ]


def excel_liste_axe_vat(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier Dictionnaire Centrale Filles/Axe Pro/TVA de facturation"""
    titre_list = file_name.split("_")
    titre = " ".join(titre_list[:-4])

    return excel_list_export(
        file_io,
        file_name,
        sheet_name='AXE PRO VS TVA',
        title=titre,
        columns=columns,
        rows=get_clean_rows(),
        orientation="landscape",
    )
