"""Module d'export des Abonnement par maisons

Commentaire:

created at: 2023-03-01
created by: Paulo ALVES

modified at: 2023-03-01
modified by: Paulo ALVES
"""

import io

from apps.core.excel_outputs.excel_writer import (
    f_entetes,
    f_ligne,
)
from apps.centers_clients.models import MaisonSubcription
from apps.core.excel_outputs.generic_list_export import excel_list_export

columns = [
    {
        "entete": "CODE MAISON",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{"align": "center"},
        },
        "width": 9,
    },
    {
        "entete": "MAISON",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{},
        },
        "width": 40,
    },
    {
        "entete": "ARTICLE",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{},
        },
        "width": 25,
    },
    {
        "entete": "QTY",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "num_format": "#,##0",
            },
        },
        "width": 8,
    },
    {
        "entete": "UNITE",
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
        "width": 7,
    },
    {
        "entete": "PRIX NET",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "num_format": "#,##0.00",
            },
        },
        "width": 9,
    },
    {
        "entete": "FONCTION",
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
        "width": 12,
    },
    {
        "entete": "ENSEIGNE",
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
        "width": 12,
    },
]


def get_clean_rows():
    """Retourne les lignes à écrire"""

    return [
        (
            row_dict.get("maison", ""),
            row_dict.get("maison__intitule", ""),
            row_dict.get("article__reference", ""),
            row_dict.get("qty", ""),
            row_dict.get("unit_weight__unity", ""),
            row_dict.get("net_unit_price", ""),
            row_dict.get("function", ""),
            row_dict.get("for_signboard", ""),
        )
        for row_dict in MaisonSubcription.objects.all().values(
            "maison",
            "maison__intitule",
            "article__reference",
            "qty",
            "unit_weight__unity",
            "net_unit_price",
            "function",
            "for_signboard",
        )
    ]


def excel_liste_subscriptions(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier de la liste des Abonnements par maisons"""
    return excel_list_export(
        file_io,
        file_name,
        sheet_name='LISTE DES ABONNEMENTS',
        title='LISTE DES ABONNEMENTS / CLIENTS',
        columns=columns,
        rows=get_clean_rows(),
    )
