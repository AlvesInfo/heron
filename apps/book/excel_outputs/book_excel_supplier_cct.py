"""Module d'export du fichier excel pour le répertoire des sociétés

Commentaire:

created at: 2022-05-12
created by: Paulo ALVES

modified at: 2022-05-12
modified by: Paulo ALVES
"""
import io

from apps.core.excel_outputs.excel_writer import (
    f_entetes,
    f_ligne,
)
from apps.book.models import Society, SupplierCct
from apps.core.excel_outputs.generic_list_export import excel_list_export

COLUMNS = [
    {
        "entete": "Maison",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "left",
            },
        },
        "width": 34,
    },
    {
        "entete": "CCT X3",
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
        "width": 10,
    },
    {
        "entete": "Identifiants",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "left",
            },
        },
        "width": 101,
    },
]


def get_rows(parmas_dict: dict):
    """Renvoie les résultats de la requête nécessaire à l'export excel
    :param parmas_dict: paramètre de la requête
    :return: resultats de la requête
    """

    return [
        (row.cct_uuid_identification.name, row.cct_uuid_identification.cct, row.cct_identifier)
        for row in SupplierCct.objects.filter(**parmas_dict).order_by(
            "cct_uuid_identification__name"
        )
    ]


def excel_liste_supplier_cct(file_io: io.BytesIO, file_name: str, parmas_dict: dict) -> dict:
    """Fonction de génération du fichier de liste des identificant pour les cct, pour un tiers X3"""
    supplier = Society.objects.get(**parmas_dict)
    titre = f"Identifiants founisseur pour les CCT : {supplier!s}"
    get_clean_rows = get_rows(parmas_dict)

    return excel_list_export(
        file_io,
        file_name,
        sheet_name=parmas_dict.get('third_party_num'),
        title=titre,
        columns=COLUMNS,
        rows=get_clean_rows,
        odd_color="#E0E0E0",
    )
