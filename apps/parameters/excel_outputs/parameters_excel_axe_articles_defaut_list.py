"""Module d'export du fichier excel pour sortie la liste des axes et catégories par défaut

Commentaire:

created at: 2023-01-19
created by: Paulo ALVES

modified at: 2023-01-19
modified by: Paulo ALVES
"""

import io

from apps.core.excel_outputs.excel_writer import (
    f_entetes,
    f_ligne,
)
from apps.parameters.models import DefaultAxeArticle
from apps.core.excel_outputs.generic_list_export import excel_list_export

columns_list = [
    {
        "entete": "Catégorie",
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
        "width": 30,
    },
    {
        "entete": "Rubrique Presta",
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
    {
        "entete": "Axe BU",
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
    {
        "entete": "Axe PRJ",
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
    {
        "entete": "Axe PYS",
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
    {
        "entete": "Axe RFA",
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


def get_row():
    """Fonction qui renvoie les bonnes colonnes pour le fichier Excel"""

    yield from [
        (
            row.big_category.__str__().replace("None", ""),
            row.sub_category.__str__().replace("None", ""),
            row.axe_bu.__str__().replace("None", ""),
            row.axe_prj.__str__().replace("None", ""),
            row.axe_pys.__str__().replace("None", ""),
            row.axe_rfa.__str__().replace("None", ""),
        )
        for row in DefaultAxeArticle.objects.filter(slug_name="axes_articles").order_by("id")
    ]


def excel_list_axe_article_defaut(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier de liste des axes et catégories par défaut"""
    titre_list = file_name.split("_")
    titre = " ".join(titre_list[:-4])

    return excel_list_export(
        file_io,
        file_name,
        sheet_name=titre[:30],
        title=titre,
        columns=columns_list,
        rows=get_row(),
        orientation="landscape",
    )
